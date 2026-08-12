from __future__ import annotations

import time
from typing import Any

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from .base import BaseAdapter
from ..browser.filler import FormFiller
from ..tracker.db import Application, ApplicationDB
from ..ui import info, warn, success, error, section, confirm


class LinkedInEasyApplyAdapter(BaseAdapter):
    """Platform adapter for LinkedIn Easy Apply job postings."""

    @classmethod
    def can_handle(cls, url: str) -> bool:
        return "linkedin.com" in url.lower()

    def apply(self, url: str, company: str = "", title: str = "", review: bool = True, auto_submit: bool = False) -> dict[str, Any]:
        if url and not url.startswith("about:") and self.page.url != url:
            if not self.page.query_selector(".job-details-jobs-unified-top-card__company-name, .jobs-apply-button"):
                info(f"Loading LinkedIn posting: {url}")
                try:
                    self.page.goto(url, wait_until="domcontentloaded")
                    time.sleep(1)
                except Exception as exc:
                    warn(f"Navigation note: {exc}")

        company = company or self._extract_company_name()
        title = title or self._extract_job_title()
        section(f"Job Application: {company} — {title}")

        # AI & Heuristic Qualification Screening
        from ..llm.screening import screen_job_qualification
        description = self._extract_job_description()
        screening = screen_job_qualification(title, company, description, self.profile)
        if not screening["qualified"]:
            warn(f"[Screening] SKIP ({screening['score']}% match): {screening['reason']}")
            return {
                "company": company,
                "title": title,
                "platform": "linkedin",
                "status": "skipped_unqualified",
                "url": url,
                "reason": screening["reason"],
            }
        else:
            success(f"[Screening] MATCH ({screening['score']}% match): {screening['reason']}")

        # Check for Easy Apply button vs External Apply button
        easy_apply_btn = self._find_easy_apply_button()
        external_apply_btn = self._find_external_apply_button() if not easy_apply_btn else None

        if not easy_apply_btn and not external_apply_btn:
            warn("No Apply button found on page.")
            return {
                "company": company,
                "title": title,
                "platform": "linkedin",
                "status": "apply_button_missing",
                "url": url,
            }

        # Handle External Company Site Redirect
        if external_apply_btn:
            info("Easy Apply modal not present. Found external company career portal link.")
            info("Clicking external application link...")
            
            # Catch new tab or page redirection
            with self.page.context.expect_page(timeout=5000) as page_info:
                try:
                    external_apply_btn.click()
                except Exception:
                    pass
            
            try:
                target_page = page_info.value
            except Exception:
                target_page = self.page.context.pages[-1] if len(self.page.context.pages) > 1 else self.page

            target_page.wait_for_load_state("domcontentloaded")
            time.sleep(2)

            info(f"Loaded external career portal: {target_page.url}")
            filler = FormFiller(target_page, self.profile)
            n_inputs = filler.fill_input_fields()

            # If 0 inputs found on landing page, click embedded Apply button/link on external page
            if n_inputs == 0:
                apply_trigger = target_page.query_selector("a[href*='apply'], button:has-text('Apply'), a:has-text('Apply'), button[aria-label*='Apply']")
                if apply_trigger and apply_trigger.is_visible():
                    info("Clicking external career page 'Apply' button to reveal form fields...")
                    try:
                        apply_trigger.click()
                        time.sleep(2)
                        n_inputs = filler.fill_input_fields()
                    except Exception as exc:
                        warn(f"External apply click note: {exc}")

            n_radios = filler.fill_radio_and_selects()
            has_file = filler.handle_file_uploads()

            success(f"External form filled: {n_inputs} input fields, {n_radios} radio choices, resume attached: {has_file}")
            if review:
                info("[Review Mode] Review filled external application in browser. Press Enter when done...")

            # Log to tracker DB
            app = Application(
                company=company,
                title=title,
                platform="external_website",
                channel="company_website",
                url=target_page.url or url,
                status="submitted" if auto_submit else "draft",
                notes="Applied via external company career site automation",
            )
            db = ApplicationDB()
            app_id = db.add(app)
            success(f"Logged application #{app_id}: {company} — {title} [external_website]")

            return {
                "id": app_id,
                "company": company,
                "title": title,
                "platform": "external_website",
                "status": "submitted" if auto_submit else "draft",
                "url": target_page.url or url,
            }

        # Handle LinkedIn Easy Apply Modal
        apply_btn = easy_apply_btn
        info("Clicking Easy Apply...")
        apply_btn.click()
        time.sleep(2)

        filler = FormFiller(self.page, self.profile)
        submitted = False
        step_count = 0
        max_steps = 15

        while step_count < max_steps:
            step_count += 1
            info(f"Processing application modal step {step_count}...")

            # Fill form fields in current step
            n_inputs = filler.fill_input_fields()
            n_radios = filler.fill_radio_and_selects()
            filler.handle_file_uploads()

            # Check for navigation buttons inside modal
            modal = self.page.query_selector(".jobs-easy-apply-modal, div[role='dialog']")
            if not modal:
                warn("Modal closed or lost.")
                break

            submit_btn = modal.query_selector("button[aria-label*='Submit'], button:has-text('Submit')")
            review_btn = modal.query_selector("button[aria-label*='Review'], button:has-text('Review')")
            next_btn = modal.query_selector("button[aria-label*='Next'], button[aria-label*='Continue'], button:has-text('Next')")

            if submit_btn or review_btn:
                info("Reached final modal step!")
                if review:
                    success("Form fields successfully populated. [Review Mode] Please review the modal in your browser.")
                    if confirm("Submit this application now?", default=False):
                        target_btn = submit_btn or review_btn
                        target_btn.click()
                        submitted = True
                        success("Application submitted successfully!")
                    else:
                        info("Submission paused by user in review mode.")
                    break
                elif auto_submit:
                    target_btn = submit_btn or review_btn
                    if target_btn:
                        target_btn.click()
                        time.sleep(1)
                        if review_btn and not submit_btn:
                            final_submit = modal.query_selector("button[aria-label*='Submit'], button:has-text('Submit')")
                            if final_submit:
                                final_submit.click()
                        submitted = True
                        success("Auto-submitted application!")
                    break

            if next_btn and next_btn.is_enabled():
                next_btn.click()
                time.sleep(1.5)
            else:
                info("No further next steps found in modal.")
                break

        # Auto-log application to tracker DB
        app_status = "submitted" if submitted else "draft"
        app = Application(
            company=company,
            title=title,
            platform="linkedin_easyapply",
            channel="linkedin",
            url=url,
            status=app_status,
            notes="Applied via autoapply LinkedIn Easy Apply adapter",
        )
        db = ApplicationDB()
        app_id = db.add(app)
        success(f"Logged application #{app_id}: {company} — {title} [{app_status}]")

        return {
            "id": app_id,
            "company": company,
            "title": title,
            "platform": "linkedin_easyapply",
            "status": app_status,
            "url": url,
        }

    def _extract_company_name(self) -> str:
        selectors = [
            ".job-details-jobs-unified-top-card__company-name",
            ".jobs-unified-top-card__company-name",
            "a.topcard__org-name-link",
            ".company-name",
        ]
        for sel in selectors:
            elem = self.page.query_selector(sel)
            if elem and elem.inner_text().strip():
                return elem.inner_text().strip()
        return "Unknown Company"

    def _extract_job_title(self) -> str:
        selectors = [
            ".job-details-jobs-unified-top-card__job-title",
            ".jobs-unified-top-card__job-title",
            "h1.t-24",
            "h1.top-card-layout__title",
        ]
        for sel in selectors:
            elem = self.page.query_selector(sel)
            if elem and elem.inner_text().strip():
                return elem.inner_text().strip()
        return "Unknown Role"

    def _extract_job_description(self) -> str:
        selectors = [
            ".job-details-jobs-unified-description__content",
            ".jobs-description__content",
            "#job-details",
            ".description__text",
            "article",
        ]
        for sel in selectors:
            elem = self.page.query_selector(sel)
            if elem and elem.inner_text().strip():
                return elem.inner_text().strip()
        return ""

    def _find_easy_apply_button(self) -> Any | None:
        selectors = [
            "button[aria-label*='Easy Apply']",
            "button:has-text('Easy Apply')",
        ]
        for sel in selectors:
            btn = self.page.query_selector(sel)
            if btn and btn.is_visible():
                return btn
        return None

    def _find_external_apply_button(self) -> Any | None:
        selectors = [
            "button[aria-label*='company website']",
            "a[aria-label*='company website']",
            "button.jobs-apply-button",
            "a.jobs-apply-button",
            "button:has-text('Apply')",
            "a:has-text('Apply')",
        ]
        for sel in selectors:
            btn = self.page.query_selector(sel)
            if btn and btn.is_visible():
                return btn
        return None
