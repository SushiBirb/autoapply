import tempfile
from pathlib import Path
import pytest

from autoapply.profile.schema import empty_profile
from autoapply.profile.seed import seeded_profile
from autoapply.tracker.db import Application, ApplicationDB


@pytest.fixture
def tmp_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture providing an isolated temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AUTOAPPLY_DATA_DIR", str(data_dir))
    return data_dir


@pytest.fixture
def test_db(tmp_path: Path) -> ApplicationDB:
    """Fixture providing a fresh isolated SQLite database instance."""
    db_path = tmp_path / "test_autoapply.db"
    return ApplicationDB(path=db_path)


@pytest.fixture
def sample_profile() -> dict:
    """Fixture providing a copy of the seeded master profile."""
    return seeded_profile()
