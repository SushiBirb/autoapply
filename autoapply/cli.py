from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

import click
from rich.table import Table
from rich.pretty import pprint

from . import __version__, ui
from .config import CHANNELS, PLATFORMS, STATUSES, DEFAULT_RESUME_PATH, RESUME_DIR
from .profile import init_profile, load_profile, profile_exists
from .tracker import Application, ApplicationDB


@click.group()
@click.version_option(__version__, prog_name="autoapply")
def main() -> None:
    """autoapply — local-first job application automation (review-before-submit)."""


@main.group()
def profile() -> None:
    """Manage your master profile (the 40-field source of truth)."""


@profile.command("init")
@click.option("--force", is_flag=True, help="Overwrite existing profile.")
def profile_init(force: bool) -> None:
    """Interactive setup. Pre-filled from your resume."""
    init_profile(force=force)


@profile.command("show")
@click.option("--section", default=None, help="Show only one section (e.g. identity, work_authorization).")
def profile_show(section: str | None) -> None:
    """Print the saved profile."""
    try:
        data = load_profile()
    except FileNotFoundError as exc:
        ui.error(str(exc))
        sys.exit(1)
    if section:
        if section not in data:
            ui.error(f"No section {section!r}. Available: {', '.join(data.keys())}")
            sys.exit(1)
        data = {section: data[section]}
    ui.section("Master profile")
    pprint(data, expand_all=True)


@profile.command("path")
def profile_path() -> None:
    """Print the on-disk profile location."""
    from .config import PROFILE_PATH
    ui.info(str(PROFILE_PATH))


@main.command()
@click.option("--company", required=True, help="Company name.")
@click.option("--title", required=True, help="Job title.")
@click.option("--platform", type=click.Choice(PLATFORMS), default="other")
@click.option("--channel", type=click.Choice(CHANNELS), default="company_website")
@click.option("--location", default="", help="Job location.")
@click.option("--url", default="", help="Posting URL.")
@click.option("--resume", "resume_version", default="", help="Which resume version you used.")
@click.option("--salary", default="", help="Posted salary / range.")
@click.option("--notes", default="", help="Free-text notes.")
@click.option("--status", type=click.Choice(STATUSES), default="submitted")
def log(company, title, platform, channel, location, url, resume_version, salary, notes, status) -> None:
    """Log a manual application to the tracker."""
    app = Application(
        company=company, title=title, platform=platform, channel=channel,
        location=location, url=url, resume_version=resume_version,
        salary=salary, notes=notes, status=status,
    )
    db = ApplicationDB()
    app_id = db.add(app)
    ui.success(f"Logged #{app_id}: {company} — {title} [{status}]")


@main.command(name="list")
@click.option("--status", type=click.Choice(STATUSES), default=None, help="Filter by status.")
@click.option("--company", default=None, help="Filter by company (substring).")
@click.option("--limit", default=50, help="Max rows.")
def list_apps(status, company, limit) -> None:
    """List tracked applications."""
    db = ApplicationDB()
    apps = db.list(status=status, company=company)[:limit]
    if not apps:
        ui.warn("No applications logged yet. Try `autoapply log --company ... --title ...`.")
        return
    table = Table(title="Applications", show_lines=False)
    table.add_column("#", style="dim")
    table.add_column("Logged")
    table.add_column("Company")
    table.add_column("Title")
    table.add_column("Platform")
    table.add_column("Status", style="bold")
    for a in apps:
        table.add_row(
            str(a.id), a.logged_at[:10], a.company, a.title, a.platform, a.status
        )
    ui.console.print(table)


@main.command()
@click.option("--status", type=click.Choice(STATUSES), required=True, help="New status.")
@click.option("--note", default="", help="Optional note.")
@click.argument("app_id", type=int)
def status(app_id, status, note) -> None:
    """Update an application's status (records a status event)."""
    db = ApplicationDB()
    if not db.get(app_id):
        ui.error(f"No application #{app_id}.")
        sys.exit(1)
    db.set_status(app_id, status, note)
    ui.success(f"#{app_id} -> {status}")


@main.command()
@click.argument("term", required=False)
def search(term) -> None:
    """Search applications by company or title."""
    db = ApplicationDB()
    apps = db.search(term) if term else db.list()
    if not apps:
        ui.warn("No matches.")
        return
    table = Table(title=f"Search: {term}")
    table.add_column("#", style="dim")
    table.add_column("Company")
    table.add_column("Title")
    table.add_column("Status")
    for a in apps:
        table.add_row(str(a.id), a.company, a.title, a.status)
    ui.console.print(table)


@main.command()
def stats() -> None:
    """Conversion metrics (segmented by status / channel / platform)."""
    db = ApplicationDB()
    s = db.stats()
    if s["total"] == 0:
        ui.warn("No applications yet — nothing to analyze.")
        return
    ui.section("Funnel")
    ui.info(f"Total applied: {s['total']}")
    ui.info(f"Responses (screen+): {s['responses']}  ({s['response_rate']:.0%})")
    ui.success(f"Offers: {s['offers']}  ({s['offer_rate']:.0%})")

    def block(title_, mapping):
        if not mapping:
            return
        table = Table(title=title_)
        table.add_column("Key")
        table.add_column("Count", justify="right")
        for key, count in sorted(mapping.items(), key=lambda kv: -kv[1]):
            table.add_row(str(key), str(count))
        ui.console.print(table)

    ui.section("Breakdown")
    block("By status", s["by_status"])
    block("By channel", s["by_channel"])
    block("By platform", s["by_platform"])


@main.command()
def doctor() -> None:
    """Check environment readiness for each phase."""
    ui.section("Environment check")
    checks = []
    checks.append(("Python", sys.version.split()[0], True))

    try:
        import yaml  # noqa: F401
        checks.append(("PyYAML", "ok", True))
    except Exception:
        checks.append(("PyYAML", "missing", False))

    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        checks.append(("Playwright Python", "installed", True))
    except Exception:
        checks.append(("Playwright Python", "missing (needed phase 2+)", False))

    try:
        import google.genai  # noqa: F401
        checks.append(("google-genai", "installed", True))
    except Exception:
        checks.append(("google-genai", "missing (needed phase 3)", False))

    checks.append(("Profile", "exists" if profile_exists() else "not created (run profile init)", profile_exists()))

    import os
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    checks.append(("Gemini API key", "set" if api_key else "not set (needed phase 3)", bool(api_key)))

    table = Table(title="Doctor")
    table.add_column("Component")
    table.add_column("Status")
    table.add_column("OK", justify="center")
    for name, status_val, ok in checks:
        table.add_row(name, status_val, "[green]yes[/green]" if ok else "[red]no[/red]")
    ui.console.print(table)


@main.command()
@click.argument("app_id", type=int)
def open_url(app_id) -> None:
    """Open the posting URL for a logged application in your browser."""
    db = ApplicationDB()
    app = db.get(app_id)
    if not app:
        ui.error(f"No application #{app_id}.")
        sys.exit(1)
    if not app.url:
        ui.error("No URL recorded for that application.")
        sys.exit(1)
    webbrowser.open(app.url)
    ui.info(f"Opening {app.url}")


@main.command()
@click.option("--site", default="linkedin", help="Site to log into (default: linkedin).")
def login(site: str) -> None:
    """Open persistent Chromium browser window to log into LinkedIn or job portals."""
    from .browser import launch_browser_session
    target_url = "https://www.linkedin.com/login" if site.lower() == "linkedin" else site
    ui.section("Persistent Session Browser Login")
    ui.info(f"Opening browser window to: {target_url}")
    ui.info("Log in with your credentials in the browser window. Session cookies will be saved automatically.")
    with launch_browser_session(headless=False) as (context, page):
        page.goto(target_url, wait_until="domcontentloaded")
        ui.info("[Interactive Mode] Log into your account in the opened browser window.")
        ui.info("Press Enter in this terminal once you are logged in...")
        input()
    ui.success("Session state saved to persistent browser profile!")


@main.command()
@click.option("--url", required=True, help="Job application URL.")
@click.option("--headless", is_flag=True, help="Run browser in headless mode.")
@click.option("--review/--no-review", default=True, help="Pause on final review modal before submitting.")
@click.option("--auto-submit", is_flag=True, help="Automatically submit without pausing for review.")
def apply(url: str, headless: bool, review: bool, auto_submit: bool) -> None:
    """Launch automated application form filling for a job posting URL."""
    from .browser import FormFiller, launch_browser_session
    from .adapters import LinkedInEasyApplyAdapter
    try:
        prof = load_profile()
    except FileNotFoundError as exc:
        ui.error(str(exc))
        sys.exit(1)

    ui.section(f"Navigating to {url}")
    with launch_browser_session(headless=headless) as (context, page):
        if LinkedInEasyApplyAdapter.can_handle(url):
            adapter = LinkedInEasyApplyAdapter(page, prof)
            adapter.apply(url, review=review, auto_submit=auto_submit)
        else:
            page.goto(url, wait_until="domcontentloaded")
            ui.info("Page loaded. Analyzing form fields...")
            filler = FormFiller(page, prof)
            n_inputs = filler.fill_input_fields()
            n_choices = filler.fill_radio_and_selects()
            ui.success(f"Form filling complete: {n_inputs} input fields, {n_choices} radio choices, file upload: {has_file}")
            if review:
                ui.info("[Review Mode] Review filled form in browser window. Press Enter when done...")
                input()


@main.group()
def credentials() -> None:
    """Manage generated company career portal login accounts & passwords."""


@credentials.command("list")
def credentials_list() -> None:
    """List all auto-generated company portal login credentials."""
    db = ApplicationDB()
    creds = db.list_credentials()
    if not creds:
        ui.info("No portal credentials saved yet. Log file is at data/portal_credentials.txt.")
        return

    table = Table(title=f"Saved Portal Credentials ({len(creds)})")
    table.add_column("Company")
    table.add_column("Portal Domain")
    table.add_column("Login Email")
    table.add_column("Password", style="green")
    table.add_column("Created At", style="dim")

    for c in creds:
        table.add_row(c["company"], c["domain"], c["email"], c["password"], c["created_at"])
    ui.console.print(table)


@credentials.command("path")
def credentials_path() -> None:
    """Print the location of the easy-to-read portal_credentials.txt file."""
    db = ApplicationDB()
    p = db.export_credentials_file()
    ui.info(str(p))


@main.command()
@click.option("--keywords", default=None, help="Job search keywords. If omitted, keywords are auto-generated from your resume.")
@click.option("--location", default="", help="Target location (e.g. 'Louisville, KY').")
@click.option("--easy-apply/--all", default=True, help="Filter for Easy Apply only or include external company website portals.")
@click.option("--exp-level", default="1,2", help="Experience level filter: 1=Internship, 2=Entry Level, 1,2=Both (default).")
@click.option("--limit", default=10, help="Max jobs to discover.")
@click.option("--headless", is_flag=True, help="Run browser in headless mode.")
@click.option("--apply-now", is_flag=True, help="Sequentially auto-fill discovered jobs after search.")
def discover(keywords: str | None, location: str, easy_apply: bool, exp_level: str, limit: int, headless: bool, apply_now: bool) -> None:
    """Discover matching job postings on LinkedIn based on resume context or custom keywords."""
    from .browser import JobDiscoveryEngine, launch_browser_session
    from .adapters import LinkedInEasyApplyAdapter
    from .llm import GeminiAnswerGenerator

    try:
        prof = load_profile()
    except FileNotFoundError as exc:
        ui.error(str(exc))
        sys.exit(1)

    search_queries: list[str] = []
    if keywords:
        search_queries = [keywords]
    else:
        ui.info("Analyzing resume profile to generate optimal job search keywords...")
        gen = GeminiAnswerGenerator(prof)
        search_queries = gen.suggest_search_keywords()
        ui.success(f"Generated search queries from resume: {', '.join(search_queries)}")

    all_jobs: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    with launch_browser_session(headless=headless) as (context, page):
        discovery = JobDiscoveryEngine(page)

        for query in search_queries:
            if len(all_jobs) >= limit:
                break
            found = discovery.search_linkedin(
                keywords=query,
                location=location,
                easy_apply_only=easy_apply,
                experience_level=exp_level,
                limit=limit - len(all_jobs),
            )
            for j in found:
                if j["url"] not in seen_urls:
                    seen_urls.add(j["url"])
                    all_jobs.append(j)

        # Smart Fallback: If strict queries returned 0 results, search broader industry terms
        if not all_jobs:
            ui.warn(f"No initial matches found for location '{location or 'Any'}'. Broadening search query...")
            broad_queries = ["Cybersecurity", "Information Security", "Network Engineer", "IT Security"]
            for b_query in broad_queries:
                if len(all_jobs) >= limit:
                    break
                found = discovery.search_linkedin(
                    keywords=b_query,
                    location=location,
                    easy_apply_only=easy_apply,
                    experience_level=exp_level,
                    limit=limit - len(all_jobs),
                )
                for j in found:
                    if j["url"] not in seen_urls:
                        seen_urls.add(j["url"])
                        all_jobs.append(j)

        if not all_jobs:
            ui.warn("No jobs found matching criteria.")
            return

        table = Table(title=f"Discovered Job Postings ({len(all_jobs)})")
        table.add_column("#", style="dim")
        table.add_column("Company")
        table.add_column("Title")
        table.add_column("Location")
        table.add_column("URL")

        for idx, j in enumerate(all_jobs, 1):
            table.add_row(str(idx), j["company"], j["title"], j["location"], j["url"])
        ui.console.print(table)

        if apply_now or ui.confirm(f"Batch fill applications for these {len(all_jobs)} jobs now?", default=False):
            ui.section("Batch Application Auto-Fill")
            adapter = LinkedInEasyApplyAdapter(page, prof)
            for j in all_jobs:
                ui.info(f"\n---> Applying to: {j['company']} — {j['title']}")
                adapter.apply(j["url"], company=j.get("company", ""), title=j.get("title", ""), review=True)


if __name__ == "__main__":
    main()
