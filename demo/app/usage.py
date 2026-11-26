"""Limits for work that calls a model.

Questions answered from the receipts on the page do not come through here.
A model question and a new read of the sample receipt do. Each visitor gets
an hourly allowance, and the whole demo gets a daily allowance. The counts
sit in a small database on the receipts volume so a restart keeps the day.
"""

from __future__ import annotations

import ipaddress
import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Request

from app.session import session_id

log = logging.getLogger(__name__)

LIMIT_MESSAGE = (
    "This demo has reached its limit for now. "
    "Please try again later, or book a short call and I'll walk you through it."
)

VISITOR_AI_QUESTIONS_PER_HOUR = 8
VISITOR_SAMPLE_READS_PER_HOUR = 4
DEMO_AI_QUESTIONS_PER_DAY = 60
DEMO_SAMPLE_READS_PER_DAY = 40

ENV_VISITOR_AI_QUESTIONS_PER_HOUR = "DEMO_VISITOR_AI_QUESTIONS_PER_HOUR"
ENV_VISITOR_SAMPLE_READS_PER_HOUR = "DEMO_VISITOR_SAMPLE_READS_PER_HOUR"
ENV_DEMO_AI_QUESTIONS_PER_DAY = "DEMO_AI_QUESTIONS_PER_DAY"
ENV_DEMO_SAMPLE_READS_PER_DAY = "DEMO_SAMPLE_READS_PER_DAY"

_LOCK = threading.Lock()
_USAGE_DB_NAME = ".demo-usage.sqlite"


def current_time() -> datetime:
    """Clock for the allowances. Tests can replace this."""
    return datetime.now(timezone.utc)


def configured_limit(name: str, default: int) -> int:
    """Read a whole-number setting, or the default when it is blank or not a number."""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return max(0, int(raw.strip()))
    except ValueError:
        return default


def forwarded_client_ip(header: str | None) -> str | None:
    """Last valid address in X-Forwarded-For.

    The edge proxy appends the address it accepted. That last entry is the
    visitor it saw. An address placed at the front does not open a new allowance.
    """
    if not header:
        return None
    parts = [part.strip() for part in header.split(",") if part.strip()]
    for raw in reversed(parts):
        ip = _normalize_ip(raw)
        if ip:
            return ip
    return None


def visitor_key(request: Request) -> str:
    """Who this allowance belongs to: the proxy address, or the browser session."""
    ip = forwarded_client_ip(request.headers.get("x-forwarded-for"))
    if ip:
        return f"ip:{ip}"
    return f"session:{session_id(request)}"


def allow_model_question(request: Request) -> bool:
    """Record one model question, or refuse when the visitor or the day is full."""
    return _reserve(
        kind="ai_question",
        visitor=visitor_key(request),
        per_hour=configured_limit(
            ENV_VISITOR_AI_QUESTIONS_PER_HOUR,
            VISITOR_AI_QUESTIONS_PER_HOUR,
        ),
        per_day=configured_limit(
            ENV_DEMO_AI_QUESTIONS_PER_DAY,
            DEMO_AI_QUESTIONS_PER_DAY,
        ),
    )


def allow_sample_read(request: Request) -> bool:
    """Record one sample read, or refuse when the visitor or the day is full."""
    return _reserve(
        kind="sample_read",
        visitor=visitor_key(request),
        per_hour=configured_limit(
            ENV_VISITOR_SAMPLE_READS_PER_HOUR,
            VISITOR_SAMPLE_READS_PER_HOUR,
        ),
        per_day=configured_limit(
            ENV_DEMO_SAMPLE_READS_PER_DAY,
            DEMO_SAMPLE_READS_PER_DAY,
        ),
    )


def usage_db_path() -> Path:
    """Database file beside the receipt JSON. The catalog only reads ``*.json``."""
    from app.main import RECEIPT_DATA_PATH

    return RECEIPT_DATA_PATH / _USAGE_DB_NAME


def _reserve(*, kind: str, visitor: str, per_hour: int, per_day: int) -> bool:
    now = current_time().astimezone(timezone.utc)
    with _LOCK:
        try:
            path = usage_db_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(path, timeout=5, isolation_level=None)
        except (sqlite3.Error, OSError):
            log.exception("Could not open demo usage records")
            return False
        try:
            conn.execute("BEGIN IMMEDIATE")
            _ensure(conn)
            _drop_old(conn, now)
            hour_start = _stamp(now - timedelta(hours=1))
            day_start = _stamp(now.replace(hour=0, minute=0, second=0, microsecond=0))
            if _count(conn, kind, visitor, hour_start) >= per_hour:
                conn.execute("ROLLBACK")
                return False
            if _count_all(conn, kind, day_start) >= per_day:
                conn.execute("ROLLBACK")
                return False
            conn.execute(
                "INSERT INTO usage_events (kind, visitor, at) VALUES (?, ?, ?)",
                (kind, visitor, _stamp(now)),
            )
            conn.execute("COMMIT")
            return True
        except (sqlite3.Error, OSError):
            log.exception("Could not record demo usage")
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            return False
        finally:
            conn.close()


def _ensure(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_events (
            kind TEXT NOT NULL,
            visitor TEXT NOT NULL,
            at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS usage_events_by_visitor
            ON usage_events (kind, visitor, at)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS usage_events_by_time
            ON usage_events (kind, at)
        """
    )


def _drop_old(conn: sqlite3.Connection, now: datetime) -> None:
    """Forget rows from earlier days so the file stays small."""
    cutoff = _stamp(now - timedelta(days=2))
    conn.execute("DELETE FROM usage_events WHERE at < ?", (cutoff,))


def _count(conn: sqlite3.Connection, kind: str, visitor: str, after: str) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) FROM usage_events
        WHERE kind = ? AND visitor = ? AND at > ?
        """,
        (kind, visitor, after),
    ).fetchone()
    return int(row[0] if row else 0)


def _count_all(conn: sqlite3.Connection, kind: str, after: str) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) FROM usage_events
        WHERE kind = ? AND at >= ?
        """,
        (kind, after),
    ).fetchone()
    return int(row[0] if row else 0)


def _stamp(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_ip(raw: str) -> str | None:
    text = raw.strip().strip('"').strip("'")
    if text.startswith("[") and "]" in text:
        text = text[1 : text.index("]")]
    elif text.count(":") == 1 and "." in text:
        text = text.rsplit(":", 1)[0]
    try:
        return str(ipaddress.ip_address(text))
    except ValueError:
        return None
