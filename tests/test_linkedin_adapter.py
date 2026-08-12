from pathlib import Path
import pytest

from autoapply.adapters.linkedin import LinkedInEasyApplyAdapter
from autoapply.browser.session import launch_browser_session
from autoapply.profile.seed import seeded_profile
from autoapply.tracker.db import ApplicationDB


def test_can_handle_linkedin_url():
    assert LinkedInEasyApplyAdapter.can_handle("https://www.linkedin.com/jobs/view/123456789") is True
    assert LinkedInEasyApplyAdapter.can_handle("https://linkedin.com/jobs/search?keywords=security") is True
    assert LinkedInEasyApplyAdapter.can_handle("https://boards.greenhouse.io/company/jobs/1234") is False
    assert LinkedInEasyApplyAdapter.can_handle("https://jobs.lever.co/company/1234") is False


def test_linkedin_easy_apply_flow_on_synthetic_modal(tmp_path: Path, tmp_data_dir: Path):
    profile_dir = tmp_path / "browser_profile"
    sample_prof = seeded_profile()

    synthetic_html = """
    <!DOCTYPE html>
    <html>
    <head><title>LinkedIn Job Posting</title></head>
    <body>
        <div class="job-details-jobs-unified-top-card__company-name">CrowdStrike</div>
        <h1 class="job-details-jobs-unified-top-card__job-title">Security Operations Center Intern</h1>
        
        <button class="jobs-apply-button">Easy Apply</button>

        <div class="jobs-easy-apply-modal" role="dialog">
            <h2>Contact Info</h2>
            <label for="first_name">First Name</label>
            <input type="text" id="first_name" name="first_name" />

            <label for="email">Email</label>
            <input type="email" id="email" name="email" />

            <button aria-label="Review application">Review</button>
        </div>
    </body>
    </html>
    """

    with launch_browser_session(user_data_dir=profile_dir, headless=True) as (context, page):
        page.set_content(synthetic_html)
        adapter = LinkedInEasyApplyAdapter(page, sample_prof)

        # Execute application workflow in non-interactive review mode
        result = adapter.apply("https://www.linkedin.com/jobs/view/99999", review=False, auto_submit=True)

        assert result["company"] == "CrowdStrike"
        assert result["title"] == "Security Operations Center Intern"
        assert result["platform"] == "linkedin_easyapply"
        assert result["status"] == "submitted"

        # Verify auto-logged into SQLite database
        db = ApplicationDB()
        apps = db.list(company="CrowdStrike")
        assert len(apps) == 1
        assert apps[0].title == "Security Operations Center Intern"
        assert apps[0].platform == "linkedin_easyapply"
