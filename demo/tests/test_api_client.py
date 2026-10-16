"""Companion API client: optional date window with a 422 fallback."""

from __future__ import annotations

from app.api_client import ApiError, ReceiptApiClient


def test_ask_sends_window_then_retries_on_422(monkeypatch) -> None:
    client = ReceiptApiClient("http://api.test")
    calls: list[dict] = []

    def fake_post(path: str, json_body: dict) -> dict:
        calls.append(json_body)
        if "start_date" in json_body:
            raise ApiError("extra fields not allowed", status_code=422)
        return {"answer": "ok"}

    monkeypatch.setattr(client, "_post", fake_post)
    result = client.ask(
        "How much did I spend per category from 2026-07-01 to 2026-08-31?",
        start_date="2026-07-01",
        end_date="2026-08-31",
    )
    assert result == {"answer": "ok"}
    assert calls[0]["start_date"] == "2026-07-01"
    assert calls[0]["end_date"] == "2026-08-31"
    assert "start_date" not in calls[1]


def test_ask_does_not_retry_other_errors(monkeypatch) -> None:
    client = ReceiptApiClient("http://api.test")

    def fake_post(path: str, json_body: dict) -> dict:
        raise ApiError("down", status_code=503)

    monkeypatch.setattr(client, "_post", fake_post)
    try:
        client.ask("hello", start_date="2026-07-01", end_date="2026-08-31")
    except ApiError as exc:
        assert exc.status_code == 503
    else:
        raise AssertionError("expected ApiError")
