from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import CHANNELS, DB_MODE, get_db_path, PLATFORMS, STATUSES

SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_at TEXT NOT NULL,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    platform TEXT,
    channel TEXT,
    location TEXT,
    url TEXT,
    status TEXT NOT NULL DEFAULT 'submitted',
    resume_version TEXT,
    salary TEXT,
    notes TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS status_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    occurred_at TEXT NOT NULL,
    status TEXT NOT NULL,
    note TEXT,
    FOREIGN KEY (application_id) REFERENCES applications(id)
);

CREATE TABLE IF NOT EXISTS portal_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    portal_domain TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_used_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_applications_company ON applications(company);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_status_events_app ON status_events(application_id);
CREATE INDEX IF NOT EXISTS idx_portal_credentials_domain ON portal_credentials(portal_domain);
"""


@dataclass
class Application:
    company: str
    title: str
    platform: str = "other"
    channel: str = "company_website"
    location: str = ""
    url: str = ""
    status: str = "submitted"
    resume_version: str = ""
    salary: str = ""
    notes: str = ""
    id: int | None = None
    logged_at: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


def _connect(path: Path | None = None) -> sqlite3.Connection:
    target = path or get_db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    os.chmod(target, DB_MODE)
    return conn


class ApplicationDB:
    def __init__(self, path: Path | None = None):
        self._path = path

    def _conn(self) -> sqlite3.Connection:
        return _connect(self._path or get_db_path())


    def add(self, app: Application) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO applications
                (logged_at, company, title, platform, channel, location, url,
                 status, resume_version, salary, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now, app.company, app.title, app.platform, app.channel,
                    app.location, app.url, app.status, app.resume_version,
                    app.salary, app.notes, now,
                ),
            )
            app_id = cur.lastrowid
            conn.execute(
                "INSERT INTO status_events (application_id, occurred_at, status, note) VALUES (?, ?, ?, ?)",
                (app_id, now, app.status, "initial log"),
            )
            return app_id

    def set_status(self, app_id: int, status: str, note: str = "") -> None:
        if status not in STATUSES:
            raise ValueError(f"Unknown status {status!r}. Valid: {STATUSES}")
        now = datetime.now().isoformat(timespec="seconds")
        with self._conn() as conn:
            conn.execute(
                "UPDATE applications SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, app_id),
            )
            conn.execute(
                "INSERT INTO status_events (application_id, occurred_at, status, note) VALUES (?, ?, ?, ?)",
                (app_id, now, status, note),
            )

    def get(self, app_id: int) -> Application | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
        return self._row_to_app(row) if row else None

    def list(self, status: str | None = None, company: str | None = None) -> list[Application]:
        query = "SELECT * FROM applications"
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if company:
            clauses.append("LOWER(company) LIKE ?")
            params.append(f"%{company.lower()}%")
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY logged_at DESC"
        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_app(r) for r in rows]

    def search(self, term: str) -> list[Application]:
        like = f"%{term.lower()}%"
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM applications WHERE LOWER(company) LIKE ? OR LOWER(title) LIKE ? ORDER BY logged_at DESC",
                (like, like),
            ).fetchall()
        return [self._row_to_app(r) for r in rows]

    def stats(self) -> dict[str, Any]:
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
            by_status = dict(
                conn.execute(
                    "SELECT status, COUNT(*) FROM applications GROUP BY status"
                ).fetchall()
            )
            by_channel = dict(
                conn.execute(
                    "SELECT channel, COUNT(*) FROM applications GROUP BY channel"
                ).fetchall()
            )
            by_platform = dict(
                conn.execute(
                    "SELECT platform, COUNT(*) FROM applications GROUP BY platform"
                ).fetchall()
            )
        responses = sum(c for s, c in by_status.items() if s in {"phone_screen", "interview", "offer"})
        offers = by_status.get("offer", 0)
        return {
            "total": total,
            "by_status": by_status,
            "by_channel": by_channel,
            "by_platform": by_platform,
            "responses": responses,
            "offers": offers,
            "response_rate": (responses / total) if total else 0.0,
            "offer_rate": (offers / total) if total else 0.0,
        }

    @staticmethod
    def _row_to_app(row: sqlite3.Row) -> Application:
        return Application(
            id=row["id"],
            company=row["company"],
            title=row["title"],
            platform=row["platform"],
            channel=row["channel"],
            location=row["location"],
            url=row["url"],
            status=row["status"],
            resume_version=row["resume_version"],
            salary=row["salary"],
            notes=row["notes"],
            logged_at=row["logged_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def valid_statuses() -> tuple[str, ...]:
        return STATUSES

    @staticmethod
    def valid_platforms() -> tuple[str, ...]:
        return PLATFORMS

    @staticmethod
    def valid_channels() -> tuple[str, ...]:
        return CHANNELS

    def get_or_create_credential(self, company: str, domain: str, email: str) -> dict[str, str]:
        """Get or generate credentials for a company career portal domain."""
        import secrets
        import string

        with _connect(self._path) as conn:
            row = conn.execute(
                "SELECT company, portal_domain, email, password FROM portal_credentials WHERE portal_domain = ?",
                (domain,),
            ).fetchone()
            now = datetime.now().isoformat(timespec="seconds")

            if row:
                conn.execute("UPDATE portal_credentials SET last_used_at = ? WHERE portal_domain = ?", (now, domain))
                return {
                    "company": row["company"],
                    "domain": row["portal_domain"],
                    "email": row["email"],
                    "password": row["password"],
                }

            # Generate strong random password for portal account
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            rand_suffix = "".join(secrets.choice(alphabet) for _ in range(12))
            password = f"App!{rand_suffix}"

            conn.execute(
                "INSERT INTO portal_credentials (company, portal_domain, email, password, created_at, last_used_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (company, domain, email, password, now, now),
            )

        self.export_credentials_file()
        return {
            "company": company,
            "domain": domain,
            "email": email,
            "password": password,
        }

    def list_credentials(self) -> list[dict[str, str]]:
        """List all generated portal credentials."""
        with _connect(self._path) as conn:
            rows = conn.execute(
                "SELECT company, portal_domain, email, password, created_at, last_used_at FROM portal_credentials ORDER BY company ASC"
            ).fetchall()
            return [
                {
                    "company": r["company"],
                    "domain": r["portal_domain"],
                    "email": r["email"],
                    "password": r["password"],
                    "created_at": r["created_at"],
                    "last_used_at": r["last_used_at"],
                }
                for r in rows
            ]

    def export_credentials_file(self) -> Path:
        """Export all portal credentials to an easy-to-read text file (data/portal_credentials.txt)."""
        from ..config import DATA_DIR
        file_path = DATA_DIR / "portal_credentials.txt"
        creds = self.list_credentials()

        lines = [
            "==================================================================",
            "                 AUTOAPPLY PORTAL CREDENTIALS LOG                  ",
            "==================================================================",
            "This file lists all account credentials generated for external    ",
            "company career portals (Workday, Taleo, Greenhouse, Lever, etc.). ",
            "==================================================================",
            "",
        ]

        if not creds:
            lines.append("No portal accounts created yet.")
        else:
            for c in creds:
                lines.append(f"Company:      {c['company']}")
                lines.append(f"Portal URL:   {c['domain']}")
                lines.append(f"Login Email:  {c['email']}")
                lines.append(f"Password:     {c['password']}")
                lines.append(f"Created At:   {c['created_at']}")
                lines.append("-" * 66)

        file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # Set secure file permissions (0o600)
        try:
            os.chmod(file_path, 0o600)
        except Exception:
            pass

        return file_path
