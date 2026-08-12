from __future__ import annotations

from typing import Any

EMPTY_ADDRESS = {
    "street": "",
    "city": "",
    "state": "",
    "postal_code": "",
    "country": "USA",
}

EMPTY_EDUCATION = {
    "institution": "",
    "degree": "",
    "major": "",
    "minor": "",
    "gpa": "",
    "start_date": "",
    "end_date": "",
    "location": "",
}

EMPTY_EXPERIENCE = {
    "company": "",
    "title": "",
    "employment_type": "",
    "location": "",
    "start_date": "",
    "end_date": "",
    "bullets": [],
    "reason_leaving": "",
}

EMPTY_SKILL = {
    "name": "",
    "years": "",
    "proficiency": "",
    "last_used": "",
}


def empty_profile() -> dict[str, Any]:
    return {
        "identity": {
            "legal_first": "",
            "legal_middle": "",
            "legal_last": "",
            "preferred_name": "",
            "pronouns": "",
            "email": "",
            "phone": "",
            "address": dict(EMPTY_ADDRESS),
            "linkedin_url": "",
            "github_url": "",
            "portfolio_url": "",
            "website_url": "",
        },
        "work_authorization": {
            "citizenship": "",
            "requires_sponsorship": "",
            "visa_type": "",
            "visa_expiration": "",
            "security_clearance": "none",
            "willing_background_check": True,
            "willing_drug_test": True,
        },
        "eeo": {
            "veteran_status": "I prefer not to say",
            "disability_status": "I prefer not to say",
            "gender": "I prefer not to say",
            "race_ethnicity": "I prefer not to say",
        },
        "education": [],
        "experience": [],
        "skills": [],
        "projects": [],
        "preferences": {
            "target_roles": [],
            "desired_salary_min": "",
            "desired_salary_max": "",
            "remote_preference": "open",
            "willing_relocate": True,
            "willing_travel_pct": "",
        },
        "screening_answers": {
            "tell_me_about_yourself_short": "",
            "tell_me_about_yourself_long": "",
            "why_interested": "",
            "why_leaving": "",
            "strengths": "",
            "weakness": "",
            "challenging_project": "",
            "notice_period": "immediate",
        },
        "references": [],
        "meta": {
            "version": 1,
            "target_season": "",
        },
    }


SIMPLE_FIELDS: list[tuple[str, str, str, bool]] = [
    ("identity", "legal_first", "Legal first name", True),
    ("identity", "legal_middle", "Legal middle name (blank if none)", False),
    ("identity", "legal_last", "Legal last name", True),
    ("identity", "preferred_name", "Preferred name", False),
    ("identity", "pronouns", "Pronouns (optional)", False),
    ("identity", "email", "Email", True),
    ("identity", "phone", "Phone", True),
    ("identity", "linkedin_url", "LinkedIn URL", True),
    ("identity", "github_url", "GitHub URL", False),
    ("identity", "portfolio_url", "Portfolio URL (optional)", False),
    ("identity", "website_url", "Personal website (optional)", False),
    ("work_authorization", "citizenship", "Citizenship (e.g. 'US Citizen')", True),
    ("work_authorization", "requires_sponsorship", "Require sponsorship now/future? (yes/no)", True),
    ("work_authorization", "visa_type", "Visa type (blank if none)", False),
    ("work_authorization", "visa_expiration", "Visa expiration (blank if none)", False),
    ("work_authorization", "security_clearance", "Security clearance (e.g. 'none', 'Secret')", False),
    ("work_authorization", "willing_background_check", "Willing to do background check? (yes/no)", True),
    ("work_authorization", "willing_drug_test", "Willing to do drug test? (yes/no)", True),
    ("preferences", "desired_salary_min", "Desired salary min (annual USD, blank for intern hourly)", False),
    ("preferences", "desired_salary_max", "Desired salary max (annual USD, blank for intern hourly)", False),
    ("preferences", "remote_preference", "Remote preference (remote/hybrid/onsite/open)", True),
    ("preferences", "willing_relocate", "Willing to relocate? (yes/no)", True),
    ("preferences", "willing_travel_pct", "Willing to travel? (percent, e.g. 25; blank for 0)", False),
]

ADDRESS_FIELDS: list[tuple[str, bool]] = [
    ("street", True),
    ("city", True),
    ("state", True),
    ("postal_code", True),
    ("country", True),
]

EEO_FIELDS: list[tuple[str, str]] = [
    ("veteran_status", "Veteran status"),
    ("disability_status", "Disability status"),
    ("gender", "Gender"),
    ("race_ethnicity", "Race / ethnicity"),
]

SCREENING_FIELDS: list[tuple[str, str]] = [
    ("tell_me_about_yourself_short", "Tell me about yourself (SHORT, ~150 words)"),
    ("tell_me_about_yourself_long", "Tell me about yourself (LONG, ~400 words)"),
    ("why_interested", "Why are you interested in this role? (reusable)"),
    ("why_leaving", "Why are you leaving / current situation?"),
    ("strengths", "Key strengths"),
    ("weakness", "A weakness + how you're improving it"),
    ("challenging_project", "Most challenging project (STAR)"),
    ("notice_period", "Notice period / availability"),
]
