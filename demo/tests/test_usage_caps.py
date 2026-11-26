"""Hourly visitor limits and daily demo limits for model calls and sample reads."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main, usage
from app.n8n_client import N8nIngestError
from app.usage import (
    DEMO_AI_QUESTIONS_PER_DAY,
    DEMO_SAMPLE_READS_PER_DAY,
    LIMIT_MESSAGE,
    VISITOR_AI_QUESTIONS_PER_HOUR,
    VISITOR_SAMPLE_READS_PER_HOUR,
    configured_limit,
    forwarded_client_ip,
)

_WINDOW = {"start": "2026-07-01", "end": "2026-08-31"}
_REACHED = "This demo has reached its limit for now."


def _ask(client: TestClient, question: str, headers: dict[str, str] | None = None):
    return client.post(
        "/ask",
        data={"question": question, **_WINDOW},
        headers=headers or {},
    )


def _read(client: TestClient, headers: dict[str, str] | None = None):
    return client.post("/ingest-sample", data=_WINDOW, headers=headers or {})


def _hide_seeds(monkeypatch: pytest.MonkeyPatch, folder: Path) -> None:
    monkeypatch.setattr(main, "SEED_DIR", folder / "no-seeds")


def _limits(
    monkeypatch: pytest.MonkeyPatch,
    *,
    questions_per_hour: int,
    questions_per_day: int,
    reads_per_hour: int,
    reads_per_day: int,
) -> None:
    monkeypatch.setenv("DEMO_VISITOR_AI_QUESTIONS_PER_HOUR", str(questions_per_hour))
    monkeypatch.setenv("DEMO_AI_QUESTIONS_PER_DAY", str(questions_per_day))
    monkeypatch.setenv("DEMO_VISITOR_SAMPLE_READS_PER_HOUR", str(reads_per_hour))
    monkeypatch.setenv("DEMO_SAMPLE_READS_PER_DAY", str(reads_per_day))


def test_python_answers_ignore_the_model_limit(client, fake_api, monkeypatch) -> None:
    _limits(
        monkeypatch,
        questions_per_hour=0,
        questions_per_day=0,
        reads_per_hour=0,
        reads_per_day=0,
    )
    html = _ask(client, "How much did I spend on snacks in August?").text
    assert fake_api.questions == []
    assert "3.50 DC on snacks in August" in html
    assert _REACHED not in html


def test_unmatched_question_does_not_call_the_model(
    client, fake_api, data_dir, monkeypatch
) -> None:
    _limits(
        monkeypatch,
        questions_per_hour=0,
        questions_per_day=0,
        reads_per_hour=0,
        reads_per_day=0,
    )
    html = _ask(client, "What is the weather today?").text
    assert fake_api.questions == []
    assert "suggested question" in html
    assert _REACHED not in html
    assert not (data_dir / ".demo-usage.sqlite").exists()


def test_visitor_hourly_cap_on_model_questions(
    client, fake_api, data_dir, monkeypatch
) -> None:
    _hide_seeds(monkeypatch, data_dir)
    _limits(
        monkeypatch,
        questions_per_hour=1,
        questions_per_day=50,
        reads_per_hour=4,
        reads_per_day=40,
    )
    first_ip = {"X-Forwarded-For": "203.0.113.10"}
    first = _ask(client, "How much did I spend per category?", first_ip)
    assert len(fake_api.questions) == 1
    assert _REACHED not in first.text

    blocked = _ask(client, "How much did I spend per category?", first_ip)
    assert len(fake_api.questions) == 1
    assert _REACHED in blocked.text
    assert "book a short call" in blocked.text

    other = TestClient(main.app)
    allowed = _ask(other, "How much did I spend per category?", {"X-Forwarded-For": "203.0.113.11"})
    assert len(fake_api.questions) == 2
    assert _REACHED not in allowed.text


def test_daily_cap_on_model_questions(client, fake_api, data_dir, monkeypatch) -> None:
    _hide_seeds(monkeypatch, data_dir)
    _limits(
        monkeypatch,
        questions_per_hour=1,
        questions_per_day=2,
        reads_per_hour=4,
        reads_per_day=40,
    )
    for address in ("203.0.113.21", "203.0.113.22"):
        html = _ask(
            TestClient(main.app),
            "How much did I spend per category?",
            {"X-Forwarded-For": address},
        ).text
        assert _REACHED not in html
    blocked = _ask(
        TestClient(main.app),
        "How much did I spend per category?",
        {"X-Forwarded-For": "203.0.113.23"},
    )
    assert len(fake_api.questions) == 2
    assert _REACHED in blocked.text


def test_model_question_cap_lifts_after_an_hour(
    client, fake_api, data_dir, monkeypatch
) -> None:
    _hide_seeds(monkeypatch, data_dir)
    _limits(
        monkeypatch,
        questions_per_hour=1,
        questions_per_day=10,
        reads_per_hour=4,
        reads_per_day=40,
    )
    clock = {"now": datetime(2026, 11, 26, 12, 0, tzinfo=timezone.utc)}
    monkeypatch.setattr(usage, "current_time", lambda: clock["now"])
    headers = {"X-Forwarded-For": "203.0.113.30"}
    assert _REACHED not in _ask(client, "A question for the model", headers).text
    assert _REACHED in _ask(client, "A question for the model", headers).text
    clock["now"] = clock["now"] + timedelta(hours=1, minutes=1)
    assert _REACHED not in _ask(client, "A question for the model", headers).text
    assert len(fake_api.questions) == 2


def test_model_question_cap_lifts_the_next_day(
    client, fake_api, data_dir, monkeypatch
) -> None:
    _hide_seeds(monkeypatch, data_dir)
    _limits(
        monkeypatch,
        questions_per_hour=10,
        questions_per_day=1,
        reads_per_hour=4,
        reads_per_day=40,
    )
    clock = {"now": datetime(2026, 11, 26, 18, 0, tzinfo=timezone.utc)}
    monkeypatch.setattr(usage, "current_time", lambda: clock["now"])
    headers = {"X-Forwarded-For": "203.0.113.31"}
    assert _REACHED not in _ask(client, "A question for the model", headers).text
    assert _REACHED in _ask(client, "A question for the model", headers).text
    clock["now"] = datetime(2026, 11, 27, 18, 0, tzinfo=timezone.utc)
    assert _REACHED not in _ask(client, "A question for the model", headers).text
    assert len(fake_api.questions) == 2


def test_missing_address_uses_the_session(
    client, fake_api, data_dir, monkeypatch
) -> None:
    _hide_seeds(monkeypatch, data_dir)
    _limits(
        monkeypatch,
        questions_per_hour=1,
        questions_per_day=10,
        reads_per_hour=4,
        reads_per_day=40,
    )
    assert _REACHED not in _ask(client, "First for this browser").text
    assert _REACHED in _ask(client, "Second for this browser").text
    assert len(fake_api.questions) == 1
    other = TestClient(main.app)
    assert _REACHED not in _ask(other, "First for another browser").text
    assert len(fake_api.questions) == 2


def test_same_address_shares_the_hourly_cap_across_sessions(
    client, fake_api, data_dir, monkeypatch
) -> None:
    _hide_seeds(monkeypatch, data_dir)
    _limits(
        monkeypatch,
        questions_per_hour=1,
        questions_per_day=10,
        reads_per_hour=4,
        reads_per_day=40,
    )
    headers = {"X-Forwarded-For": "198.51.100.8, 203.0.113.40"}
    assert _REACHED not in _ask(client, "From this address", headers).text
    other = TestClient(main.app)
    blocked = _ask(other, "From this address again", headers)
    assert _REACHED in blocked.text
    assert len(fake_api.questions) == 1
    # A different last address is a different visitor, even with the same front value.
    fresh = _ask(
        TestClient(main.app),
        "From another address",
        {"X-Forwarded-For": "198.51.100.8, 203.0.113.41"},
    )
    assert _REACHED not in fresh.text
    assert len(fake_api.questions) == 2


def test_visitor_hourly_cap_on_sample_reads(client, fake_n8n, monkeypatch, sample_id) -> None:
    _limits(
        monkeypatch,
        questions_per_hour=8,
        questions_per_day=60,
        reads_per_hour=1,
        reads_per_day=20,
    )
    headers = {"X-Forwarded-For": "203.0.113.50"}
    assert _REACHED not in _read(client, headers).text
    assert fake_n8n.calls == [sample_id]
    other = TestClient(main.app)
    blocked = _read(other, headers)
    assert _REACHED in blocked.text
    assert "book a short call" in blocked.text
    assert fake_n8n.calls == [sample_id]
    third = _read(TestClient(main.app), {"X-Forwarded-For": "203.0.113.51"})
    assert _REACHED not in third.text
    assert fake_n8n.calls == [sample_id, sample_id]


def test_daily_cap_on_sample_reads(client, fake_n8n, monkeypatch, sample_id) -> None:
    _limits(
        monkeypatch,
        questions_per_hour=8,
        questions_per_day=60,
        reads_per_hour=1,
        reads_per_day=2,
    )
    for address in ("203.0.113.61", "203.0.113.62"):
        html = _read(TestClient(main.app), {"X-Forwarded-For": address}).text
        assert _REACHED not in html
    blocked = _read(TestClient(main.app), {"X-Forwarded-For": "203.0.113.63"})
    assert _REACHED in blocked.text
    assert fake_n8n.calls == [sample_id, sample_id]


def test_saved_sample_does_not_read_again(
    client, fake_n8n, monkeypatch, sample_id
) -> None:
    _limits(
        monkeypatch,
        questions_per_hour=8,
        questions_per_day=60,
        reads_per_hour=1,
        reads_per_day=1,
    )
    headers = {"X-Forwarded-For": "203.0.113.70"}
    first = _read(client, headers)
    assert fake_n8n.calls == [sample_id]
    assert "Green Basket Market" in first.text
    second = _read(client, headers)
    assert fake_n8n.calls == [sample_id]
    assert _REACHED not in second.text
    assert "Bananas" in second.text
    stranger = _read(TestClient(main.app), headers)
    assert _REACHED in stranger.text
    assert fake_n8n.calls == [sample_id]


def test_a_missing_saved_file_is_read_again(client, fake_n8n, data_dir, monkeypatch) -> None:
    _limits(
        monkeypatch,
        questions_per_hour=8,
        questions_per_day=60,
        reads_per_hour=5,
        reads_per_day=5,
    )
    _read(client)
    (data_dir / fake_n8n.filename).unlink()
    _read(client)
    assert len(fake_n8n.calls) == 2


def test_a_failed_read_still_counts(client, fake_n8n, monkeypatch) -> None:
    _limits(
        monkeypatch,
        questions_per_hour=8,
        questions_per_day=60,
        reads_per_hour=1,
        reads_per_day=5,
    )

    def fail(sample_id: str) -> dict:
        fake_n8n.calls.append(sample_id)
        raise N8nIngestError("webhook down")

    monkeypatch.setattr(fake_n8n, "trigger_sample", fail)
    headers = {"X-Forwarded-For": "203.0.113.77"}
    first = _read(client, headers)
    assert "webhook down" in first.text
    second = _read(client, headers)
    assert _REACHED in second.text
    assert len(fake_n8n.calls) == 1


def test_usage_counts_are_stored_beside_the_receipts(
    client, fake_api, data_dir, monkeypatch
) -> None:
    _hide_seeds(monkeypatch, data_dir)
    _limits(
        monkeypatch,
        questions_per_hour=1,
        questions_per_day=1,
        reads_per_hour=4,
        reads_per_day=40,
    )
    headers = {"X-Forwarded-For": "203.0.113.80"}
    _ask(client, "How much did I spend per category?", headers)
    db = data_dir / ".demo-usage.sqlite"
    assert db.is_file()
    rows = sqlite3.connect(db).execute(
        "SELECT kind, visitor FROM usage_events"
    ).fetchall()
    assert ("ai_question", "ip:203.0.113.80") in rows
    assert _REACHED in _ask(client, "How much did I spend per category?", headers).text
    assert len(fake_api.questions) == 1


def test_storage_trouble_blocks_the_model_call(
    client, fake_api, data_dir, monkeypatch
) -> None:
    _hide_seeds(monkeypatch, data_dir)
    monkeypatch.setattr(usage, "usage_db_path", lambda: Path("/dev/null/usage.sqlite"))
    html = _ask(client, "How much did I spend per category?").text
    assert fake_api.questions == []
    assert _REACHED in html


def test_limit_message_is_plain_words() -> None:
    assert LIMIT_MESSAGE == (
        "This demo has reached its limit for now. "
        "Please try again later, or book a short call and I'll walk you through it."
    )
    assert "—" not in LIMIT_MESSAGE
    assert "TTL" not in LIMIT_MESSAGE
    assert "simulation" not in LIMIT_MESSAGE.lower()


def test_a_blank_or_invalid_setting_uses_the_default(monkeypatch) -> None:
    monkeypatch.delenv("DEMO_VISITOR_AI_QUESTIONS_PER_HOUR", raising=False)
    assert configured_limit("DEMO_VISITOR_AI_QUESTIONS_PER_HOUR", 8) == 8
    monkeypatch.setenv("DEMO_VISITOR_AI_QUESTIONS_PER_HOUR", "nope")
    assert configured_limit("DEMO_VISITOR_AI_QUESTIONS_PER_HOUR", 8) == 8
    monkeypatch.setenv("DEMO_VISITOR_AI_QUESTIONS_PER_HOUR", "0")
    assert configured_limit("DEMO_VISITOR_AI_QUESTIONS_PER_HOUR", 8) == 0


def test_forwarded_for_uses_the_address_the_proxy_added() -> None:
    assert forwarded_client_ip(None) is None
    assert forwarded_client_ip("   ") is None
    assert forwarded_client_ip("not-an-address") is None
    assert forwarded_client_ip("203.0.113.5") == "203.0.113.5"
    assert forwarded_client_ip("198.51.100.9, 203.0.113.5") == "203.0.113.5"
    assert forwarded_client_ip("203.0.113.5:443") == "203.0.113.5"
    assert forwarded_client_ip("203.0.113.5, [2001:db8::8]") == "2001:db8::8"


def test_documented_defaults_match_the_app() -> None:
    root = Path(__file__).resolve().parents[2]
    example = (root / ".env.example").read_text(encoding="utf-8")
    compose = (root / "deploy" / "docker-compose.yml").read_text(encoding="utf-8")
    deploy = (root / "DEPLOYMENT.md").read_text(encoding="utf-8")
    pairs = (
        ("DEMO_VISITOR_AI_QUESTIONS_PER_HOUR", VISITOR_AI_QUESTIONS_PER_HOUR),
        ("DEMO_VISITOR_SAMPLE_READS_PER_HOUR", VISITOR_SAMPLE_READS_PER_HOUR),
        ("DEMO_AI_QUESTIONS_PER_DAY", DEMO_AI_QUESTIONS_PER_DAY),
        ("DEMO_SAMPLE_READS_PER_DAY", DEMO_SAMPLE_READS_PER_DAY),
    )
    section = deploy.split("### Demo usage limits", 1)[1].split("\n## ", 1)[0]
    start = example.index("# Questions answered from the receipts on the page")
    end = example.index("DEMO_SAMPLE_READS_PER_DAY=40")
    notes = example[start:end]
    for name, value in pairs:
        assert f"{name}={value}" in example
        assert "${" + f"{name}:-{value}" + "}" in compose
        assert f"| `{name}` | {value} |" in section
    for text in (section, notes):
        assert "TTL" not in text
        assert "simulation" not in text.lower()
