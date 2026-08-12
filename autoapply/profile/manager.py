from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from .. import ui
from ..config import PROFILE_MODE, PROFILE_PATH
from .seed import seeded_profile
from .schema import (
    ADDRESS_FIELDS,
    EEO_FIELDS,
    SCREENING_FIELDS,
    SIMPLE_FIELDS,
)


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"yes", "y", "true", "1"}


def _ask_yes_no(label: str, default: Any) -> bool:
    default_bool = _coerce_bool(default)
    return ui.confirm(f"{label}", default=default_bool)


def _section_identity(profile: dict) -> None:
    ui.section("Identity")
    ident = profile["identity"]
    for section, key, label, required in SIMPLE_FIELDS:
        if section != "identity":
            continue
        current = ident.get(key, "")
        value = ui.ask(label, default=str(current) if current else None)
        if value or not required:
            ident[key] = value

    ui.section("Home address")
    addr = ident["address"]
    for key, required in ADDRESS_FIELDS:
        current = addr.get(key, "")
        value = ui.ask(f"Address: {key}", default=str(current) if current else None)
        if value or not required:
            addr[key] = value


def _section_auth(profile: dict) -> None:
    ui.section("Work authorization (critical for internship applications)")
    auth = profile["work_authorization"]
    for section, key, label, required in SIMPLE_FIELDS:
        if section != "work_authorization":
            continue
        current = auth.get(key, "")
        if key in {"willing_background_check", "willing_drug_test"}:
            auth[key] = _ask_yes_no(label, current)
        else:
            value = ui.ask(label, default=str(current) if current else None)
            if value or not required:
                auth[key] = value

    sponsorship = auth.get("requires_sponsorship")
    if sponsorship in {"", None}:
        ui.warn("Sponsorship answer is required by most internship forms.")
        auth["requires_sponsorship"] = "no" if _ask_yes_no("Do you require visa sponsorship?", False) is False else "yes"


def _section_eeo(profile: dict) -> None:
    ui.section("EEO (optional; defaults to 'prefer not to say')")
    if not ui.confirm("Fill in EEO fields now? (skippable)", default=False):
        return
    eeo = profile["eeo"]
    for key, label in EEO_FIELDS:
        current = eeo.get(key, "I prefer not to say")
        value = ui.ask(label, default=current)
        eeo[key] = value or current


def _section_preferences(profile: dict) -> None:
    ui.section("Preferences")
    prefs = profile["preferences"]
    for section, key, label, required in SIMPLE_FIELDS:
        if section != "preferences":
            continue
        current = prefs.get(key, "")
        if key in {"willing_relocate"}:
            prefs[key] = _ask_yes_no(label, current)
        else:
            value = ui.ask(label, default=str(current) if current else None)
            if value or not required:
                prefs[key] = value

    roles = prefs.get("target_roles") or []
    ui.info(f"Target roles seeded: {', '.join(roles) if roles else '(none)'}")
    if ui.confirm("Edit target roles?", default=False):
        roles_str = ui.ask("Comma-separated target roles", default=", ".join(roles))
        prefs["target_roles"] = [r.strip() for r in roles_str.split(",") if r.strip()]


def _section_screening(profile: dict) -> None:
    ui.section("Screening answer bank (reusable; editable later)")
    ui.info("Leave blank to skip for now. Phase 3 (Gemini) can draft these from your resume.")
    answers = profile["screening_answers"]
    for key, label in SCREENING_FIELDS:
        current = answers.get(key, "")
        value = ui.ask(f"{label} (blank to skip)", default=str(current) if current else None)
        if value:
            answers[key] = value


def _section_references(profile: dict) -> None:
    ui.section("References (optional; many internships do not require)")
    if not profile.get("references"):
        profile["references"] = []
    if not ui.confirm("Add a reference now? (skippable)", default=False):
        return
    while True:
        ref = {
            "name": ui.ask("Reference name", default=None),
            "relationship": ui.ask("Relationship", default=None),
            "email": ui.ask("Email", default=None),
            "phone": ui.ask("Phone (optional)", default=None),
        }
        if ref["name"]:
            profile["references"].append(ref)
        if not ui.confirm("Add another reference?", default=False):
            break


def init_profile(force: bool = False) -> dict:
    if PROFILE_PATH.exists() and not force:
        ui.warn(f"Profile already exists at {PROFILE_PATH}")
        if not ui.confirm("Re-run init and overwrite?", default=False):
            return load_profile()

    ui.section("autoapply profile setup")
    ui.info(f"Pre-filled from your resume. Defaults shown in [dim]\\[brackets][/dim].")
    ui.info(f"Press Enter to accept a default. Profile will be saved to: {PROFILE_PATH}")

    profile = seeded_profile()

    _section_identity(profile)
    _section_auth(profile)
    _section_eeo(profile)
    _section_preferences(profile)
    _section_screening(profile)
    _section_references(profile)

    save_profile(profile)
    ui.success(f"\nProfile saved to {PROFILE_PATH}")
    ui.info("Edit it anytime with: autoapply profile edit")
    return profile


def save_profile(profile: dict, path: Path | None = None) -> None:
    target = path or PROFILE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    with open(tmp, "w") as fh:
        yaml.safe_dump(profile, fh, sort_keys=False, default_flow_style=False, allow_unicode=True)
    os.chmod(tmp, PROFILE_MODE)
    tmp.replace(target)


def load_profile(path: Path | None = None) -> dict:
    target = path or PROFILE_PATH
    if not target.exists():
        raise FileNotFoundError(
            f"No profile found at {target}. Run `autoapply profile init` first."
        )
    with open(target) as fh:
        return yaml.safe_load(fh)


def profile_exists() -> bool:
    return PROFILE_PATH.exists()
