from pathlib import Path
import pytest

from autoapply.browser.discovery import JobDiscoveryEngine
from autoapply.browser.session import launch_browser_session


def test_job_discovery_on_synthetic_search_page(tmp_path: Path):
    profile_dir = tmp_path / "browser_profile"

    synthetic_search_html = """
    <!DOCTYPE html>
    <html>
    <head><title>LinkedIn Job Search</title></head>
    <body>
        <ul class="jobs-search-results__list">
            <li class="jobs-search-results__list-item">
                <div class="job-card-container">
                    <a class="job-card-container__link" href="/jobs/view/100000001?refId=xyz">
                        <span class="job-card-list__title">Cybersecurity Specialist</span>
                    </a>
                    <div class="job-card-container__primary-description">Palo Alto Networks</div>
                    <div class="job-card-container__metadata-item">Louisville, KY</div>
                </div>
            </li>
            <li class="jobs-search-results__list-item">
                <div class="job-card-container">
                    <a class="job-card-container__link" href="/jobs/view/100000002?refId=abc">
                        <span class="job-card-list__title">Network Engineering Intern</span>
                    </a>
                    <div class="job-card-container__primary-description">Cisco Systems</div>
                    <div class="job-card-container__metadata-item">Remote</div>
                </div>
            </li>
        </ul>
    </body>
    </html>
    """

    import urllib.parse
    data_url = "data:text/html;charset=utf-8," + urllib.parse.quote(synthetic_search_html)

    with launch_browser_session(user_data_dir=profile_dir, headless=True) as (context, page):
        page.goto(data_url)
        discovery = JobDiscoveryEngine(page)

        # Discovered listings from synthetic DOM
        jobs = discovery.search_linkedin(keywords="Cybersecurity", location="Louisville, KY", limit=5)
        assert len(jobs) >= 2
        assert jobs[0]["company"] == "Palo Alto Networks"
        assert jobs[0]["title"] == "Cybersecurity Specialist"
        assert jobs[0]["url"] == "https://www.linkedin.com/jobs/view/100000001"

        assert jobs[1]["company"] == "Cisco Systems"
        assert jobs[1]["title"] == "Network Engineering Intern"
        assert jobs[1]["url"] == "https://www.linkedin.com/jobs/view/100000002"
