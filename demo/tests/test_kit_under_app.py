"""Kit and static files stay reachable when the browser prefix is /app.

Caddy strips /app before proxying, so the app sees /demo-kit and /static.
ROOT_PATH is read when this module loads. Reloading with it set is what
catches a regression that passes the prefix into FastAPI as root_path.
"""

from __future__ import annotations

import importlib

import pytest
from app import main
from fastapi.testclient import TestClient

_GET_REDIRECTS = ("/ask", "/ingest", "/ingest-sample", "/live-import/delete")


class _QuietApi:
    """Stand-in so the home page does not wait on the real API."""

    def health(self) -> dict[str, str]:
        return {"status": "ok"}

    def summary(self, start_date: str, end_date: str) -> dict[str, object]:
        return {"total_spend": 0, "by_category": []}


@pytest.fixture
def client_under_app(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Rebuild the app the way production starts: ROOT_PATH=/app."""
    monkeypatch.setenv("ROOT_PATH", "/app")
    try:
        reloaded = importlib.reload(main)
        monkeypatch.setattr(reloaded, "api", _QuietApi())
        monkeypatch.setattr(reloaded, "RECEIPT_DATA_PATH", tmp_path)
        yield TestClient(reloaded.app)
    finally:
        monkeypatch.delenv("ROOT_PATH", raising=False)
        importlib.reload(main)


def test_kit_and_static_files_load_under_the_app_prefix(client_under_app: TestClient) -> None:
    css = client_under_app.get("/demo-kit/demo-kit.css")
    assert css.status_code == 200
    assert len(css.content) > 100

    icon = client_under_app.get("/demo-kit/favicon.svg")
    assert icon.status_code == 200
    assert b"<svg" in icon.content

    static = client_under_app.get("/static/panels/shared.css")
    assert static.status_code == 200
    assert "--bg:" in static.text

    html = client_under_app.get("/").text
    assert 'href="/app/demo-kit/demo-kit.css"' in html
    assert 'href="/app/demo-kit/favicon.svg"' in html
    assert 'src="/app/demo-kit/theme-init.js"' in html
    assert 'src="/app/demo-kit/theme.js"' in html
    assert 'action="/app/ask"' in html

    for path in _GET_REDIRECTS:
        redirect = client_under_app.get(path, follow_redirects=False)
        assert redirect.status_code == 303
        assert redirect.headers["location"] == "/app/"

    home = main._home_redirect(start="2026-07-01", end="2026-08-31", example="lumen")
    assert home.status_code == 303
    location = home.headers["location"]
    assert location.startswith("/app/?")
    assert "start=2026-07-01" in location
    assert "end=2026-08-31" in location
    assert "example=lumen" in location
