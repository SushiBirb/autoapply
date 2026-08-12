from __future__ import annotations

import time
import urllib.parse
import re
from typing import Any

from playwright.sync_api import Page
from ..ui import info, warn, success, section


class JobDiscoveryEngine:
    """Automated job posting discovery and search engine."""

    def __init__(self, page: Page):
        self.page = page

    def search_linkedin(
        self,
        keywords: str,
        location: str = "",
        easy_apply_only: bool = True,
        experience_level: str = "1,2",  # 1=Internship, 2=Entry Level
        limit: int = 15,
    ) -> list[dict[str, str]]:
        """Search LinkedIn jobs and collect posting URLs matching criteria."""
        # Sanitize keyword query to avoid slashes or extra filter text in job title input
        clean_kw = keywords.split("/")[0]
        clean_kw = re.sub(r"\b(easy\s*apply|filter|intern|internship|entry\s*level)\b", "", clean_kw, flags=re.IGNORECASE)
        clean_kw = re.sub(r"[^\w\s\-]", "", clean_kw).strip()
        clean_kw = " ".join(clean_kw.split())

        params = {"keywords": clean_kw}
        if location:
            params["location"] = location
        if easy_apply_only:
            params["f_AL"] = "true"  # Filter for Easy Apply
        if experience_level:
            params["f_E"] = experience_level  # Filter for Internship (1) and Entry Level (2)

        query_str = urllib.parse.urlencode(params)
        search_url = f"https://www.linkedin.com/jobs/search/?{query_str}"

        section(f"Searching LinkedIn Jobs: {clean_kw} ({location or 'Any Location'})")
        # Navigate to new search URL if current page URL differs from target search URL
        if self.page.url != search_url and not self.page.url.startswith("data:"):
            info(f"Navigating to {search_url}")
            try:
                self.page.goto(search_url, wait_until="domcontentloaded")
                time.sleep(2.5)
            except Exception as exc:
                warn(f"Search navigation note: {exc}")

        # Scroll down to trigger lazy loading of search cards
        for _ in range(3):
            self.page.evaluate("window.scrollBy(0, 800)")
            time.sleep(0.8)

        results: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        # Strategy 1: Container cards with live clicking & description screening
        job_cards = self.page.query_selector_all(".job-card-container, .jobs-search-results__list-item, li.base-card, .job-search-card")

        from ..llm.screening import screen_job_qualification

        for card in job_cards:
            if len(results) >= limit:
                break

            link_elem = card.query_selector("a.job-card-container__link, a.base-card__full-link, a[href*='/jobs/view/']")
            title_elem = card.query_selector(".job-card-list__title, .base-card__title, .job-search-card__title")
            company_elem = card.query_selector(".job-card-container__primary-description, .base-card__subtitle, .job-search-card__company-name")
            loc_elem = card.query_selector(".job-card-container__metadata-item, .job-search-card__location")

            if link_elem:
                href = link_elem.get_attribute("href") or ""
                clean_url = href.split("?")[0] if href else ""
                if clean_url.startswith("/"):
                    clean_url = "https://www.linkedin.com" + clean_url
                if clean_url and clean_url not in seen_urls and "/jobs/view/" in clean_url:
                    seen_urls.add(clean_url)
                    job_title = title_elem.inner_text().strip() if title_elem else "Unknown Title"
                    company_name = company_elem.inner_text().strip() if company_elem else "Unknown Company"
                    job_loc = loc_elem.inner_text().strip() if loc_elem else (location or "")

                    # Click on job card in list panel to load right detail pane
                    description = ""
                    try:
                        if not self.page.url.startswith("data:"):
                            card.scroll_into_view_if_needed()
                            link_elem.click()
                            time.sleep(1.0)

                        desc_elem = self.page.query_selector(".jobs-search__job-details, .jobs-description-content, .jobs-description__content, #job-details, article")
                        if desc_elem and desc_elem.inner_text().strip():
                            description = desc_elem.inner_text().strip()
                    except Exception as exc:
                        warn(f"Card selection note: {exc}")

                    # Screen qualification from description text
                    screening = screen_job_qualification(job_title, company_name, description)
                    if not screening["qualified"]:
                        warn(f"  [Skipped {screening['score']}% Match] {company_name} — {job_title} ({screening['reason']})")
                        continue

                    success(f"  [Qualified {screening['score']}% Match] {company_name} — {job_title}")
                    results.append({
                        "title": job_title,
                        "company": company_name,
                        "location": job_loc,
                        "url": clean_url,
                    })

        # Strategy 2: Direct href links fallback if container selectors didn't catch all
        if len(results) < limit:
            all_links = self.page.query_selector_all("a[href*='/jobs/view/']")
            for link in all_links:
                if len(results) >= limit:
                    break
                href = link.get_attribute("href") or ""
                clean_url = href.split("?")[0] if href else ""
                if clean_url.startswith("/"):
                    clean_url = "https://www.linkedin.com" + clean_url
                if clean_url and clean_url not in seen_urls and "/jobs/view/" in clean_url:
                    seen_urls.add(clean_url)
                    t_text = link.inner_text().strip()
                    job_title = t_text if t_text and len(t_text) > 3 else "Security / IT Role"
                    results.append({
                        "title": job_title,
                        "company": "LinkedIn Listing",
                        "location": location or "Louisville, KY",
                        "url": clean_url,
                    })

        success(f"Discovered {len(results)} matching job postings.")
        return results
