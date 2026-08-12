from pathlib import Path
from autoapply.llm.screening import screen_job_qualification
from autoapply.profile import load_profile


def test_screening_qualified_entry_role(tmp_path: Path):
    profile = load_profile()
    
    result = screen_job_qualification(
        job_title="Cybersecurity Specialist / Intern",
        company="Palo Alto Networks",
        description="Looking for an Entry Level Information Security Analyst with knowledge of Linux, Azure, and Python.",
        profile=profile,
    )

    assert result["qualified"] is True
    assert result["score"] >= 80
    assert result["status"] == "qualified"


def test_screening_unqualified_senior_role(tmp_path: Path):
    profile = load_profile()
    
    result = screen_job_qualification(
        job_title="Senior Director of Information Security & Enterprise Architecture",
        company="Global Enterprise",
        description="Requires 10+ years leading enterprise InfoSec teams and CISSP certification.",
        profile=profile,
    )

    assert result["qualified"] is False
    assert result["score"] <= 30
    assert result["status"] == "unqualified_senior"
