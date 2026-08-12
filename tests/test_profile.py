from pathlib import Path
import pytest

from autoapply.profile.schema import empty_profile
from autoapply.profile.seed import seeded_profile
from autoapply.profile.manager import save_profile, load_profile, profile_exists


def test_empty_profile_structure():
    prof = empty_profile()
    assert "identity" in prof
    assert "work_authorization" in prof
    assert "eeo" in prof
    assert "preferences" in prof
    assert "screening_answers" in prof
    assert prof["identity"]["legal_first"] == ""


def test_seeded_profile():
    prof = seeded_profile()
    assert prof["identity"]["legal_first"] == "Joshua"
    assert prof["identity"]["legal_last"] == "Mattingly"
    assert prof["identity"]["email"] == "jmattingly@proitserv.com"
    assert "certifications" in prof
    assert "CompTIA Security+" in prof["certifications"]
    assert "InfoSec Intern" in prof["preferences"]["target_roles"]


def test_save_and_load_profile(tmp_path: Path):
    target_path = tmp_path / "master.yaml"
    prof = seeded_profile()
    prof["identity"]["preferred_name"] = "Josh Test"

    save_profile(prof, path=target_path)
    assert target_path.exists()

    loaded = load_profile(path=target_path)
    assert loaded["identity"]["preferred_name"] == "Josh Test"
    assert loaded["identity"]["legal_first"] == "Joshua"


def test_load_nonexistent_profile(tmp_path: Path):
    target_path = tmp_path / "nonexistent.yaml"
    with pytest.raises(FileNotFoundError):
        load_profile(path=target_path)
