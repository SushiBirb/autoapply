from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "autoapply"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_data_dir() -> Path:
    d = Path(os.environ.get("AUTOAPPLY_DATA_DIR", PROJECT_ROOT / "data"))
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_db_path() -> Path:
    return get_data_dir() / "autoapply.db"

def get_profile_path() -> Path:
    return get_data_dir() / "master.yaml"

def get_answers_path() -> Path:
    return get_data_dir() / "answers.yaml"

def get_resume_dir() -> Path:
    return get_data_dir() / "resume"

def get_audit_log_path() -> Path:
    return get_data_dir() / "audit.log"

class _ConfigProxy:
    @property
    def DATA_DIR(self) -> Path:
        return get_data_dir()

    @property
    def PROFILE_PATH(self) -> Path:
        return get_profile_path()

    @property
    def ANSWERS_PATH(self) -> Path:
        return get_answers_path()

    @property
    def DB_PATH(self) -> Path:
        return get_db_path()

    @property
    def RESUME_DIR(self) -> Path:
        return get_resume_dir()

    @property
    def AUDIT_LOG(self) -> Path:
        return get_audit_log_path()

_proxy = _ConfigProxy()
DATA_DIR = _proxy.DATA_DIR
PROFILE_PATH = _proxy.PROFILE_PATH
ANSWERS_PATH = _proxy.ANSWERS_PATH
DB_PATH = _proxy.DB_PATH
RESUME_DIR = _proxy.RESUME_DIR
AUDIT_LOG = _proxy.AUDIT_LOG


PROFILE_MODE = 0o600
DB_MODE = 0o600

DEFAULT_RESUME_PATH = Path.home() / "2026-Q3-condensed.pdf"

PLATFORMS = (
    "greenhouse",
    "lever",
    "ashby",
    "workday",
    "linkedin_easyapply",
    "indeed",
    "handshake",
    "other",
)

CHANNELS = (
    "company_website",
    "linkedin",
    "indeed",
    "handshake",
    "referral",
    "recruiter",
    "job_board",
    "other",
)

STATUSES = (
    "submitted",
    "phone_screen",
    "interview",
    "offer",
    "rejected",
    "withdrawn",
    "ghosted",
)
