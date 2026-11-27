"""Live imports are scoped to the visitor session cookie, not the shared volume."""

from __future__ import annotations

from app import main
from app.sample_receipt import MERCHANT
from app.session import IMPORTS_COOKIE, SESSION_COOKIE
from fastapi.testclient import TestClient


def test_get_home_sets_session_cookie(client) -> None:
    response = client.get("/")
    assert SESSION_COOKIE in response.cookies
    assert IMPORTS_COOKIE in response.cookies
    raw = response.cookies[IMPORTS_COOKIE].strip('"')
    assert raw == ""


def test_fresh_session_does_not_see_another_visitors_import(client, fake_n8n, data_dir) -> None:
    first = client.post("/ingest-sample", data={"start": "2026-07-01", "end": "2026-08-31"})
    assert MERCHANT in first.text
    assert fake_n8n.filename in first.cookies.get(IMPORTS_COOKIE, "")

    other = TestClient(main.app)
    html = other.get("/").text
    # The new-receipt label is on every page. The other visitor's lines are not.
    assert 'id="live-panel"' not in html
    assert "Bananas" not in html
    assert "Just added" not in html
    assert "25.00 DC" not in html
    # File is still on the shared volume.
    assert (data_dir / fake_n8n.filename).is_file()


def test_same_session_still_sees_its_import(client, fake_n8n) -> None:
    client.post("/ingest-sample", data={"start": "2026-07-01", "end": "2026-08-31"})
    html = client.get("/").text
    assert MERCHANT in html
    assert 'id="live-panel"' in html


def test_remove_hides_import_for_this_session_only(client, fake_n8n, data_dir) -> None:
    client.post("/ingest-sample", data={"start": "2026-07-01", "end": "2026-08-31"})
    stem = fake_n8n.filename.removesuffix(".json")
    response = client.post(
        "/live-import/delete",
        data={
            "example": f"live-{stem}",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
        follow_redirects=True,
    )
    assert 'id="live-panel"' not in response.text
    assert "Bananas" not in response.text
    assert "Just added" not in response.text
    assert fake_n8n.filename not in (response.cookies.get(IMPORTS_COOKIE) or "")
    assert (data_dir / fake_n8n.filename).is_file()
