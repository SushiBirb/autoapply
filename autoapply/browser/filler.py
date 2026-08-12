from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from playwright.sync_api import ElementHandle, Page

from ..ui import info, warn, success


class FormFiller:
    """Intelligent DOM form field analyzer and auto-filler."""

    def __init__(self, page: Page, profile: dict[str, Any]):
        self.page = page
        self.profile = profile
        from ..llm import GeminiAnswerGenerator
        self.llm_generator = GeminiAnswerGenerator(profile)

    def fill_input_fields(self) -> int:
        """Find and fill standard text, email, tel, address, password, and text area fields."""
        filled_count = 0
        inputs = self.page.query_selector_all("input[type='text'], input[type='email'], input[type='tel'], input[type='password'], input:not([type]), textarea")

        # Extract domain & company for portal credential generation
        page_url = self.page.url or ""
        domain = page_url.split("/")[2] if "/" in page_url and len(page_url.split("/")) > 2 else "company_portal"
        company_name = domain.replace("www.", "").split(".")[0].title()
        user_email = self.profile.get("identity", {}).get("email", "candidate@proitserv.com")

        for elem in inputs:
            if not elem.is_visible() or elem.is_disabled():
                continue

            label_text = self._extract_label(elem)
            input_type = elem.get_attribute("type") or ""

            if input_type == "password" or "password" in label_text.lower():
                from ..tracker.db import ApplicationDB
                db = ApplicationDB()
                cred = db.get_or_create_credential(company=company_name, domain=domain, email=user_email)
                value_to_fill = cred["password"]
                info(f"  Generated & logged portal password for {company_name} ({domain}) -> Saved to data/portal_credentials.txt")
            else:
                value_to_fill = self._match_profile_value(label_text, elem)

            # If no direct profile match, check if it's an open-ended screening question
            if not value_to_fill and (input_type == "textarea" or len(label_text) > 15):
                value_to_fill = self.llm_generator.generate_answer(label_text)

            if value_to_fill:
                current_val = elem.input_value() if input_type != "textarea" else elem.inner_text()
                if not current_val.strip():
                    elem.fill(str(value_to_fill))
                    filled_count += 1
                    info(f"  Filled {label_text!r} -> {str(value_to_fill)[:30]!r}")

        return filled_count

    def fill_radio_and_selects(self) -> int:
        """Handle work authorization, relocation, and yes/no radio buttons/dropdowns."""
        count = 0
        auth = self.profile.get("work_authorization", {})
        sponsorship = auth.get("requires_sponsorship", "no").lower() == "yes"
        background = auth.get("willing_background_check", True)
        drug_test = auth.get("willing_drug_test", True)
        relocate = self.profile.get("preferences", {}).get("willing_relocate", True)

        fieldsets = self.page.query_selector_all("fieldset, div[role='radiogroup'], div.form-group, div.form-row")
        for fs in fieldsets:
            legend_elem = fs.query_selector("legend, label, h3, h4, span.label")
            legend_text = legend_elem.inner_text().lower() if legend_elem else ""
            fs_text = ((fs.inner_text() or "") + " " + legend_text).lower()

            if any(k in fs_text for k in ["sponsorship", "authorized", "legally", "background", "relocate", "citizenship"]):
                target_choice = None
                if "sponsorship" in fs_text:
                    target_choice = "yes" if sponsorship else "no"
                elif "authorized" in fs_text or "legally" in fs_text or "citizenship" in fs_text:
                    target_choice = "yes"
                elif "background" in fs_text:
                    target_choice = "yes" if background else "no"
                elif "relocate" in fs_text:
                    target_choice = "yes" if relocate else "no"

                if target_choice:
                    radios = fs.query_selector_all("input[type='radio']")
                    for r in radios:
                        lbl = self._extract_label(r).lower()
                        if (target_choice == "yes" and "yes" in lbl) or (target_choice == "no" and "no" in lbl):
                            if not r.is_checked():
                                r.check(force=True)
                                count += 1
                                info(f"  Checked radio choice for {fs_text[:30]!r} -> {lbl!r}")
                            break
        return count

    def handle_file_uploads(self, resume_path: Path | str | None = None) -> bool:
        """Handle resume file upload fields."""
        file_inputs = self.page.query_selector_all("input[type='file']")
        if not file_inputs:
            return False

        path_to_upload = Path(resume_path) if resume_path else None
        if not path_to_upload or not path_to_upload.exists():
            # Check default resume path or data/resume/
            from ..config import DEFAULT_RESUME_PATH, get_resume_dir
            if DEFAULT_RESUME_PATH.exists():
                path_to_upload = DEFAULT_RESUME_PATH
            else:
                resume_files = list(get_resume_dir().glob("*.pdf"))
                if resume_files:
                    path_to_upload = resume_files[0]

        if path_to_upload and path_to_upload.exists():
            for inp in file_inputs:
                if inp.is_visible() or True:  # file inputs are often hidden visually
                    inp.set_input_files(str(path_to_upload))
                    success(f"  Uploaded resume: {path_to_upload.name}")
                    return True
        else:
            warn("  No resume PDF found to upload.")
        return False

    def _extract_label(self, elem: ElementHandle) -> str:
        """Extract descriptive label for a form element."""
        # 1. Associated <label for="...">
        elem_id = elem.get_attribute("id")
        if elem_id:
            label_elem = self.page.query_selector(f"label[for='{elem_id}']")
            if label_elem and label_elem.inner_text().strip():
                return label_elem.inner_text().strip()

        # 2. Parent label text
        try:
            parent_text = self.page.evaluate("(el) => el.closest('label')?.innerText || ''", elem)
            if parent_text and parent_text.strip():
                return parent_text.strip()
        except Exception:
            pass

        # 3. aria-label or placeholder or value (for radio/checkbox)
        aria = elem.get_attribute("aria-label")
        if aria:
            return aria.strip()
        
        placeholder = elem.get_attribute("placeholder")
        if placeholder:
            return placeholder.strip()

        val = elem.get_attribute("value")
        if val and elem.get_attribute("type") in {"radio", "checkbox"}:
            return val.strip()

        name = elem.get_attribute("name")
        if name:
            return name.strip()

        return ""

    def _match_profile_value(self, label_text: str, elem: ElementHandle) -> str | None:
        """Match field label against candidate profile fields."""
        lbl = label_text.lower()
        ident = self.profile.get("identity", {})
        addr = ident.get("address", {})

        if any(k in lbl for k in ["first name", "given name", "first_name"]):
            return ident.get("legal_first", "")
        if any(k in lbl for k in ["last name", "surname", "family name", "last_name"]):
            return ident.get("legal_last", "")
        if any(k in lbl for k in ["middle name", "middle_name"]):
            return ident.get("legal_middle", "")
        if any(k in lbl for k in ["preferred name", "nickname"]):
            return ident.get("preferred_name", "")
        if "email" in lbl:
            return ident.get("email", "")
        if any(k in lbl for k in ["phone", "mobile", "telephone", "cell"]):
            return ident.get("phone", "")
        if "linkedin" in lbl:
            return ident.get("linkedin_url", "")
        if "github" in lbl:
            return ident.get("github_url", "")
        if "portfolio" in lbl or "website" in lbl:
            return ident.get("portfolio_url") or ident.get("website_url", "")
        if any(k in lbl for k in ["street", "address line 1", "street address"]):
            return addr.get("street", "")
        if "city" in lbl:
            return addr.get("city", "")
        if any(k in lbl for k in ["state", "province"]):
            return addr.get("state", "")
        if any(k in lbl for k in ["zip", "postal", "postal code"]):
            return addr.get("postal_code", "")

        return None
