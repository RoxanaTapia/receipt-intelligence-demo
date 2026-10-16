"""Visitor page: chips, one-click extract, labels, and Q&A window passing."""

from __future__ import annotations

from app.main import _parse_window
from app.questions import SUGGESTED_QUESTIONS
from app.sample_receipt import MERCHANT


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
    for item in SUGGESTED_QUESTIONS:
        assert item["label"] in html
        assert f'data-question="{item["question"]}"' in html


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
    assert "Source: category totals on demo receipts" in response.text


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


def test_ask_drinks_in_august_chip_stays_in_august(client, fake_api) -> None:
    response = client.post(
        "/ask",
        data={
            "question": "How much did I spend on drinks in August?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    )
    sent = fake_api.questions[0]["question"]
    assert sent == "How much did I spend on drinks in August 2026?"
    assert "4.10 DC" in response.text
    assert "Source: drinks on demo receipts in August 2026" in response.text


def test_ingest_sample_one_click(client, fake_n8n, sample_id) -> None:
    response = client.post(
        "/ingest-sample",
        data={"start": "2026-07-01", "end": "2026-08-31"},
    )
    assert response.status_code == 200
    assert fake_n8n.calls == [sample_id]
    html = response.text
    assert MERCHANT in html
    assert "Extracted" in html
    assert "Use sample receipt" in html
    assert "Extracting…" in html
    assert "already in the corpus" not in html
    assert 'data-scroll="live-ingest"' in html
    # Live result is the review card; seed table and extra chrome stay out of the way.
    assert html.count('class="receipt-heading"') == 0
    assert "cat-chip" in html
    assert html.count("DC demo data") == 1
    assert "Remove live import" not in html
    assert "Examples and spending window" not in html
    assert "Lumen Pantry" not in html


def test_extracted_view_hides_spending_footer(client, fake_api, fake_n8n) -> None:
    html = client.post(
        "/ingest-sample", data={"start": "2026-07-01", "end": "2026-08-31"}
    ).text
    assert "already in the corpus" not in html
    assert "Examples and spending window" not in html
    assert "totals did not change" not in html


def test_live_selection_does_not_duplicate_main_receipt(
    client, fake_n8n
) -> None:
    client.post("/ingest-sample", data={"start": "2026-07-01", "end": "2026-08-31"})
    stem = fake_n8n.filename.removesuffix(".json")
    html = client.get(f"/?example=live-{stem}").text
    assert MERCHANT in html
    assert 'class="receipt-heading"' not in html
    assert 'id="live-panel"' in html


def test_demo_css_includes_new_rules() -> None:
    from app.main import DEMO_CSS

    assert ".ask-chip" in DEMO_CSS
    assert ".sample-one-click" in DEMO_CSS
    assert "--accent:" in DEMO_CSS
    assert "Inter" in DEMO_CSS
    assert "1400px" in DEMO_CSS
    assert "font-size: 18px" in DEMO_CSS


def test_ask_after_extract_matches_on_screen_receipt(
    client, fake_api, fake_n8n
) -> None:
    client.post("/ingest-sample", data={"start": "2026-07-01", "end": "2026-08-31"})
    fake_api.questions.clear()
    html = client.post(
        "/ask",
        data={
            "question": "How much did I spend per category?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    ).text
    assert fake_api.questions == []
    assert "15.00 DC" in html
    assert "4.40 DC" in html
    assert "5.60 DC" in html
    assert "25.00 DC" in html
    assert "21.20" not in html
    assert "16.10" not in html
    assert "5.10 DC" not in html
    assert "July" not in html
    assert "snacks" not in html.lower()
    assert "Source: Green Basket Market, 2026-08-15." in html


def test_ask_drinks_after_extract_matches_receipt(
    client, fake_api, fake_n8n
) -> None:
    client.post("/ingest-sample", data={"start": "2026-07-01", "end": "2026-08-31"})
    fake_api.questions.clear()
    html = client.post(
        "/ask",
        data={
            "question": "How much did I spend on drinks in August?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    ).text
    assert fake_api.questions == []
    assert "4.40 DC" in html
    assert "4.10 DC" not in html
    assert "Source: Green Basket Market, 2026-08-15." in html
