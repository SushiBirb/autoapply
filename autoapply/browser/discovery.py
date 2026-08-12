from __future__ import annotations

import time
import urllib.parse
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
        limit: int = 15,
    ) -> list[dict[str, str]]:
        """Search LinkedIn jobs and collect posting URLs matching criteria."""
        # Sanitize keyword query to avoid slashes or extra filter text in job title input
        keywords = keywords.split("/")[0]
        import re
        keywords = re.sub(r"\b(easy\s*apply|filter)\b", "", keywords, flags=re.IGNORECASE)
        keywords = re.sub(r"[^\w\s\-]", "", keywords).strip()
        keywords = " ".join(keywords.split())

        params = {"keywords": keywords}
        if location:
            params["location"] = location
        if easy_apply_only:
            params["f_AL"] = "true"  # Filter for Easy Apply

        query_str = urllib.parse.urlencode(params)
        search_url = f"https://www.linkedin.com/jobs/search/?{query_str}"

        section(f"Searching LinkedIn Jobs: {keywords} ({location or 'Any Location'})")
        if not self.page.query_selector(".jobs-search-results__list-item, .job-card-container, li.base-card"):
            info(f"Navigating to {search_url}")
            try:
                self.page.goto(search_url, wait_until="domcontentloaded")
                time.sleep(2)
            except Exception as exc:
                warn(f"Search navigation note: {exc}")

        # Scroll down to load job cards
        for _ in range(3):
            self.page.evaluate("window.scrollBy(0, 800)")
            time.sleep(1)

        job_cards = self.page.query_selector_all(".job-card-container, .jobs-search-results__list-item, li.base-card")
        results: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        for card in job_cards:
            if len(results) >= limit:
                break

            link_elem = card.query_selector("a.job-card-container__link, a.base-card__full-link, a[href*='/jobs/view/']")
            title_elem = card.query_selector(".job-card-list__title, .base-card__title")
            company_elem = card.query_selector(".job-card-container__primary-description, .base-card__subtitle")
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
                    job_loc = loc_elem.inner_text().strip() if loc_elem else ""

                    results.append({
                        "title": job_title,
                        "company": company_name,
                        "location": job_loc,
                        "url": clean_url,
                    })

        success(f"Discovered {len(results)} matching job postings.")
        return results
