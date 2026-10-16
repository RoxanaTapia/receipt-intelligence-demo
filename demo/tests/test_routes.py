"""Visitor page: chips, one-click extract, labels, and Q&A window passing."""

from __future__ import annotations

from app.main import _parse_window
from app.questions import SUGGESTED_QUESTIONS


def test_parse_window_falls_back_to_demo_span() -> None:
    start, end = _parse_window(None, None)
    assert start == "2026-07-01"
    assert end == "2026-08-31"


def test_parse_window_swaps_reversed_dates() -> None:
    start, end = _parse_window("2026-08-31", "2026-07-01")
    assert start == "2026-07-01"
    assert end == "2026-08-31"


def test_home_has_chips_extract_label_and_dc_hint(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "Run live ingest" not in html
    assert "Extract receipt" in html
    assert "Use sample receipt" in html
    assert "demo currency" in html.lower()
    assert "initDemo" in html
    for prompt in SUGGESTED_QUESTIONS:
        assert prompt in html
        assert f'data-question="{prompt}"' in html


def test_home_explains_dc_near_seed_totals(client) -> None:
    html = client.get("/").text
    assert "Lumen Pantry" in html
    assert "DC" in html
    assert "demo currency (not real money)" in html
    assert html.lower().count("demo currency") >= 2


def test_ask_undated_question_sends_visible_window(client, fake_api) -> None:
    response = client.post(
        "/ask",
        data={
            "question": "How much did I spend per category?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    )
    assert response.status_code == 200
    assert fake_api.questions, "API ask() was not called"
    sent = fake_api.questions[0]
    assert "2026-07-01" in sent["question"]
    assert "2026-08-31" in sent["question"]
    assert sent["start_date"] == "2026-07-01"
    assert sent["end_date"] == "2026-08-31"
    assert "5.10 DC" in response.text
    assert 'id="ask-answer"' in response.text
    assert 'data-scroll="ask-answer"' in response.text


def test_ask_category_month_only_adds_year(client, fake_api) -> None:
    client.post(
        "/ask",
        data={
            "question": "How much did I spend on drinks in July?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    )
    sent = fake_api.questions[0]["question"]
    assert sent == "How much did I spend on drinks in July 2026?"


def test_ingest_sample_one_click(client, fake_n8n, sample_id) -> None:
    response = client.post(
        "/ingest-sample",
        data={"start": "2026-07-01", "end": "2026-08-31"},
    )
    assert response.status_code == 200
    assert fake_n8n.calls == [sample_id]
    html = response.text
    assert "Demo Cafe" in html
    assert "Extracted" in html
    assert "Use sample receipt" in html
    assert "already in the corpus" not in html
    assert 'data-scroll="live-ingest"' in html
    # Seed receipt stays in the main pane; live result is only in the live panel.
    assert "Lumen Pantry" in html
    assert html.count('class="receipt-heading"') == 1


def test_rerun_copy_is_friendly_when_totals_do_not_move(
    client, fake_api, fake_n8n
) -> None:
    response = client.post("/ingest-sample", data={"start": "2026-07-01", "end": "2026-08-31"})
    html = response.text
    assert "already in the corpus" not in html
    assert "already in the demo" in html
    assert "totals did not change" in html


def test_live_selection_does_not_duplicate_main_receipt(
    client, fake_n8n
) -> None:
    client.post("/ingest-sample", data={"start": "2026-07-01", "end": "2026-08-31"})
    stem = fake_n8n.filename.removesuffix(".json")
    html = client.get(f"/?example=live-{stem}").text
    assert "Demo Cafe" in html
    assert 'class="receipt-heading"' not in html
    assert 'id="live-panel"' in html


def test_demo_css_includes_new_rules() -> None:
    from app.main import DEMO_CSS

    assert ".ask-chip" in DEMO_CSS
    assert ".sample-one-click" in DEMO_CSS
