from pathlib import Path
import pytest

from autoapply.browser.session import launch_browser_session
from autoapply.browser.filler import FormFiller
from autoapply.profile.seed import seeded_profile


def test_browser_session_launch(tmp_path: Path):
    profile_dir = tmp_path / "browser_profile"
    with launch_browser_session(user_data_dir=profile_dir, headless=True) as (context, page):
        assert page is not None
        page.set_content("<html><body><h1>autoapply browser test</h1></body></html>")
        assert "autoapply browser test" in page.content()


def test_form_filler_on_synthetic_form(tmp_path: Path):
    profile_dir = tmp_path / "browser_profile"
    sample_prof = seeded_profile()

    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Synthetic Job Application Form</title></head>
    <body>
        <form id="job-app">
            <label for="first_name">First Name</label>
            <input type="text" id="first_name" name="first_name" />

            <label for="last_name">Last Name</label>
            <input type="text" id="last_name" name="last_name" />

            <label for="email">Email Address</label>
            <input type="email" id="email" name="email" />

            <label for="phone">Phone Number</label>
            <input type="tel" id="phone" name="phone" />

            <fieldset>
                <legend>Are you legally authorized to work in the United States?</legend>
                <label><input type="radio" name="auth" value="yes" /> Yes</label>
                <label><input type="radio" name="auth" value="no" /> No</label>
            </fieldset>

            <label for="resume">Upload Resume</label>
            <input type="file" id="resume" name="resume" accept=".pdf" />
        </form>
    </body>
    </html>
    """

    with launch_browser_session(user_data_dir=profile_dir, headless=True) as (context, page):
        page.set_content(html_content)
        filler = FormFiller(page, sample_prof)

        filled_inputs = filler.fill_input_fields()
        assert filled_inputs >= 4

        # Verify values in DOM
        assert page.input_value("#first_name") == "Joshua"
        assert page.input_value("#last_name") == "Mattingly"
        assert page.input_value("#email") == "jmattingly@proitserv.com"
        assert page.input_value("#phone") == "(502) 309-1990"

        filled_radios = filler.fill_radio_and_selects()
        assert filled_radios >= 1
        assert page.is_checked("input[value='yes']")
