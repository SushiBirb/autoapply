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

CREATE INDEX IF NOT EXISTS idx_applications_company ON applications(company);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_status_events_app ON status_events(application_id);
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
