"""Visitor session cookie so live imports are scoped per browser.

Receipt JSON still lands on the shared volume (n8n persist). Deleting those
files would drop another visitor's sample, so this demo never unlinks them.
A fresh browser gets a new cookie and an empty owned-file list — the page
looks clean even if yesterday's extract is still on disk.
"""

from __future__ import annotations

import re
import secrets
from pathlib import Path

from fastapi import Request, Response

SESSION_COOKIE = "demo_session"
IMPORTS_COOKIE = "demo_live"
COOKIE_MAX_AGE = 60 * 60 * 12  # one invite / Loom visit
_SAFE_SESSION = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
_SAFE_FILE = re.compile(r"^[0-9A-Za-z._-]+\.json$")


def new_session_id() -> str:
    """URL-safe token for the visitor cookie."""
    return secrets.token_urlsafe(16)


def session_id(request: Request) -> str:
    """Return the inbound session id, or mint one when the cookie is missing."""
    raw = (request.cookies.get(SESSION_COOKIE) or "").strip()
    if _SAFE_SESSION.match(raw):
        return raw
    return new_session_id()


def owned_filenames(request: Request) -> set[str]:
    """Live-import basenames this browser ingested (from the cookie)."""
    raw = request.cookies.get(IMPORTS_COOKIE) or ""
    names: set[str] = set()
    for part in raw.split("|"):
        name = Path(part.strip()).name
        if _SAFE_FILE.match(name):
            names.add(name)
    return names


def remember_import(owned: set[str], filename: str | None) -> set[str]:
    """Add a persisted receipt to this session's visible set."""
    if not filename:
        return set(owned)
    name = Path(filename).name
    if not _SAFE_FILE.match(name):
        return set(owned)
    return set(owned) | {name}


def forget_import(owned: set[str], filename: str | None) -> set[str]:
    """Hide a live import from this session without touching the shared volume."""
    if not filename:
        return set(owned)
    name = Path(filename).name
    return {item for item in owned if item != name}


def apply_session_cookies(response: Response, sid: str, owned: set[str]) -> None:
    """Write session + owned-file cookies onto a page response."""
    cookie_kw = {
        "max_age": COOKIE_MAX_AGE,
        "httponly": True,
        "samesite": "lax",
        "path": "/",
    }
    response.set_cookie(SESSION_COOKIE, sid, **cookie_kw)
    response.set_cookie(IMPORTS_COOKIE, "|".join(sorted(owned)), **cookie_kw)
