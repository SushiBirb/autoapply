from __future__ import annotations

import re
from typing import Any

from ..ui import info, warn, success, section


def screen_job_qualification(
    job_title: str,
    company: str,
    description: str,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Screen job posting details against candidate profile to evaluate qualification match."""
    title_lower = job_title.lower()
    desc_lower = description.lower()

    # 1. Negative Seniority Flags (Senior / Director / Executive / 8+ years)
    senior_patterns = [
        r"\bsenior\b", r"\bsr\.\b", r"\bsr\b", r"\blead\b", r"\bprincipal\b",
        r"\bdirector\b", r"\bvp\b", r"\bhead of\b", r"\bmanager\b", r"\barchitect\b",
        r"\b10\+ years\b", r"\b8\+ years\b", r"\b7\+ years\b", r"\b6\+ years\b",
    ]
    is_senior = any(re.search(p, title_lower) for p in senior_patterns)

    # 2. Positive Entry / Student / Co-op Flags
    entry_patterns = [
        r"\bintern\b", r"\binternship\b", r"\bco-op\b", r"\bcoop\b", r"\bassociate\b",
        r"\bentry\b", r"\bjunior\b", r"\bjr\b", r"\banalyst\b", r"\bspecialist\b",
        r"\btechnician\b", r"\bengineer i\b", r"\bengineer 1\b", r"\bconsultant\b",
    ]
    is_entry = any(re.search(p, title_lower) for p in entry_patterns)

    # 3. Domain Relevance Flags (InfoSec, Cybersecurity, Network, IT)
    domain_patterns = [
        "security", "cyber", "infosec", "network", "it", "systems",
        "soc", "threat", "vulnerability", "cloud", "active directory",
        "entra", "azure", "proxmox", "linux", "python",
    ]
    domain_matches = sum(1 for p in domain_patterns if p in title_lower or p in desc_lower)

    # Determine match score
    if is_senior and not is_entry:
        score = 25
        status = "unqualified_senior"
        reason = f"Role requires senior leadership / high experience level (Title: {job_title})."
    elif is_entry or domain_matches >= 2:
        score = 85
        status = "qualified"
        reason = f"Strong match for candidate CIS / InfoSec & Network Engineering track record."
    elif domain_matches == 1:
        score = 65
        status = "qualified"
        reason = "Moderate match for IT / Systems coursework background."
    else:
        score = 40
        status = "marginal"
        reason = "Low keyword domain match in job description."

    is_qualified = score >= 50

    return {
        "qualified": is_qualified,
        "score": score,
        "status": status,
        "reason": reason,
        "job_title": job_title,
        "company": company,
    }
