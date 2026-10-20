"""Local SQLite state: competitions, run history, submissions.

This is the engine's memory across the 24-hour cycle. It is deliberately
boring and dependency-free; the Vercel sync layer (engine/vercel_sync.py)
mirrors a *read-only projection* of it for the frontend, never the raw DB.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .settings import Settings, load

SCHEMA = """
CREATE TABLE IF NOT EXISTS competitions (
    slug            TEXT PRIMARY KEY,
    title           TEXT,
    metric          TEXT,
    higher_is_better INTEGER DEFAULT 1,
    target_score    REAL,
    status          TEXT DEFAULT 'registered',
    source          TEXT DEFAULT 'kaggle',
    created_at      TEXT,
    updated_at      TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    slug         TEXT NOT NULL,
    attempt      INTEGER NOT NULL,
    phase        TEXT NOT NULL,
    status       TEXT NOT NULL,
    cv_mean      REAL,
    cv_std       REAL,
    lb_score     REAL,
    score_reached INTEGER,
    session_id   TEXT,
    log_path     TEXT,
    notes        TEXT,
    started_at   TEXT,
    finished_at  TEXT
);

CREATE TABLE IF NOT EXISTS submissions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    slug         TEXT NOT NULL,
    message      TEXT,
    public_score REAL,
    submitted_at TEXT
);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connection(settings: Settings | None = None) -> Iterator[sqlite3.Connection]:
    settings = settings or load()
    settings.state_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


# --- competitions ------------------------------------------------------------

def register_competition(
    slug: str,
    title: str | None = None,
    metric: str | None = None,
    higher_is_better: bool = True,
    target_score: float | None = None,
    source: str = "kaggle",
    settings: Settings | None = None,
) -> None:
    now = utcnow()
    with connection(settings) as conn:
        conn.execute(
            """
            INSERT INTO competitions (slug, title, metric, higher_is_better,
                                      target_score, status, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'registered', ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title           = COALESCE(excluded.title, competitions.title),
                metric          = COALESCE(excluded.metric, competitions.metric),
                higher_is_better = excluded.higher_is_better,
                target_score    = COALESCE(excluded.target_score, competitions.target_score),
                updated_at      = excluded.updated_at
            """,
            (slug, title, metric, int(higher_is_better), target_score, source, now, now),
        )


def get_competition(slug: str, settings: Settings | None = None) -> dict[str, Any] | None:
    with connection(settings) as conn:
        row = conn.execute("SELECT * FROM competitions WHERE slug = ?", (slug,)).fetchone()
        return dict(row) if row else None


def list_competitions(settings: Settings | None = None) -> list[dict[str, Any]]:
    with connection(settings) as conn:
        rows = conn.execute("SELECT * FROM competitions ORDER BY slug").fetchall()
        return [dict(r) for r in rows]


def set_status(slug: str, status: str, settings: Settings | None = None) -> None:
    with connection(settings) as conn:
        conn.execute(
            "UPDATE competitions SET status = ?, updated_at = ? WHERE slug = ?",
            (status, utcnow(), slug),
        )


# --- runs --------------------------------------------------------------------

def start_run(slug: str, attempt: int, phase: str, notes: str | None = None,
              settings: Settings | None = None) -> int:
    with connection(settings) as conn:
        cur = conn.execute(
            "INSERT INTO runs (slug, attempt, phase, status, notes, started_at) "
            "VALUES (?, ?, ?, 'running', ?, ?)",
            (slug, attempt, phase, notes, utcnow()),
        )
        return int(cur.lastrowid)


def finish_run(
    run_id: int,
    status: str,
    cv_mean: float | None = None,
    cv_std: float | None = None,
    lb_score: float | None = None,
    score_reached: bool | None = None,
    session_id: str | None = None,
    log_path: str | None = None,
    notes: str | None = None,
    settings: Settings | None = None,
) -> None:
    with connection(settings) as conn:
        conn.execute(
            """
            UPDATE runs SET status = ?, cv_mean = ?, cv_std = ?, lb_score = ?,
                            score_reached = ?, session_id = COALESCE(?, session_id),
                            log_path = COALESCE(?, log_path),
                            notes = COALESCE(?, notes), finished_at = ?
            WHERE id = ?
            """,
            (status, cv_mean, cv_std, lb_score,
             None if score_reached is None else int(score_reached),
             session_id, log_path, notes, utcnow(), run_id),
        )


def history(slug: str, limit: int = 50, settings: Settings | None = None) -> list[dict[str, Any]]:
    with connection(settings) as conn:
        rows = conn.execute(
            "SELECT * FROM runs WHERE slug = ? ORDER BY id DESC LIMIT ?",
            (slug, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def best_run(slug: str, settings: Settings | None = None) -> dict[str, Any] | None:
    """Best *completed successful* run by CV score, honouring metric direction."""
    comp = get_competition(slug, settings) or {}
    order = "DESC" if comp.get("higher_is_better", 1) else "ASC"
    with connection(settings) as conn:
        row = conn.execute(
            f"SELECT * FROM runs WHERE slug = ? AND status = 'done' AND cv_mean IS NOT NULL "
            f"ORDER BY cv_mean {order} LIMIT 1",
            (slug,),
        ).fetchone()
        return dict(row) if row else None


def next_attempt(slug: str, settings: Settings | None = None) -> int:
    with connection(settings) as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(attempt), 0) + 1 AS n FROM runs WHERE slug = ?",
            (slug,),
        ).fetchone()
        return int(row["n"])


def recent_runs(limit: int = 10, settings: Settings | None = None) -> list[dict[str, Any]]:
    with connection(settings) as conn:
        rows = conn.execute(
            "SELECT slug, attempt, phase, status, cv_mean, lb_score, score_reached, "
            "started_at, finished_at FROM runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def cycle_stats(settings: Settings | None = None) -> dict[str, Any]:
    with connection(settings) as conn:
        competitions = conn.execute("SELECT COUNT(*) AS n FROM competitions").fetchone()["n"]
        runs = conn.execute("SELECT COUNT(*) AS n FROM runs").fetchone()["n"]
        done = conn.execute(
            "SELECT COUNT(*) AS n FROM competitions WHERE status = 'solved'"
        ).fetchone()["n"]
        last = conn.execute(
            "SELECT slug, phase, status, finished_at FROM runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return {
            "competitions": competitions,
            "runs": runs,
            "solved": done,
            "last_run": dict(last) if last else None,
        }


# --- submissions -------------------------------------------------------------

def log_submission(slug: str, message: str, public_score: float | None,
                   settings: Settings | None = None) -> None:
    with connection(settings) as conn:
        conn.execute(
            "INSERT INTO submissions (slug, message, public_score, submitted_at) "
            "VALUES (?, ?, ?, ?)",
            (slug, message, public_score, utcnow()),
        )


def submissions(slug: str, settings: Settings | None = None) -> list[dict[str, Any]]:
    with connection(settings) as conn:
        rows = conn.execute(
            "SELECT * FROM submissions WHERE slug = ? ORDER BY id DESC", (slug,)
        ).fetchall()
        return [dict(r) for r in rows]


def submissions_today(slug: str, settings: Settings | None = None) -> int:
    """Successful submissions logged for this slug since UTC midnight.

    ``submitted_at`` is an ISO-8601 UTC string, so a plain ``>= 'YYYY-MM-DD'``
    comparison is correct (rule R9: respect the daily limit).
    """
    day_start = datetime.now(timezone.utc).date().isoformat()
    with connection(settings) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM submissions WHERE slug = ? AND submitted_at >= ?",
            (slug, day_start),
        ).fetchone()
        return int(row["n"]) if row is not None else 0
