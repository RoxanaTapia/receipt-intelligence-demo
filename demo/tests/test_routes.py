"""Visitor page: chips, extract, Your receipts, and catalog-scoped answers."""

from __future__ import annotations

from app.main import _parse_window
from app.page import parse_posted_step
from app.questions import SUGGESTED_QUESTIONS
from app.sample_receipt import MERCHANT


def _step_class(html: str, step: int) -> str:
    nav = html.split('id="flow-nav"', 1)[1].split("</ol>", 1)[0]
    items = nav.split("<li")[1:]
    opener = items[step - 1].split(">", 1)[0]
    if 'class="' not in opener:
        return ""
    return opener.split('class="', 1)[1].split('"', 1)[0]


def test_parse_window_falls_back_to_demo_span() -> None:
    start, end = _parse_window(None, None)
    assert start == "2026-07-01"
    assert end == "2026-08-31"


def test_parse_window_swaps_reversed_dates() -> None:
    start, end = _parse_window("2026-08-31", "2026-07-01")
    assert start == "2026-07-01"
    assert end == "2026-08-31"


def test_home_has_chips_and_extract_label(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "Run live ingest" not in html
    assert "Extract receipt" in html
    assert "Use sample receipt" in html
    assert "Reading your receipt…" in html
    assert "initDemo" in html
    assert "fillAskQuestion" in html
    assert "setReading" in html
    assert "markAskStep" in html
    for item in SUGGESTED_QUESTIONS:
        assert item["label"] in html
        assert f'data-question="{item["question"]}"' in html


def test_home_shows_seed_receipts_and_drops_dc(client) -> None:
    html = client.get("/").text
    assert "Your receipts" in html
    assert "Lumen Pantry" in html
    assert "Harbor Home" in html
    assert "Corner Bakery" in html
    assert "$18.90" in html
    assert "$14.20" in html
    assert "$21.40" in html
    assert "Just added" not in html
    assert 'id="ask-btn" class="btn-secondary"' in html
    assert "Use sample receipt" in html
    assert "Sample added" not in html
    assert "DC demo data" not in html
    assert " DC" not in html
    assert "Examples and spending window" not in html
    assert "Remove live import" not in html
    ask_btn = html.find('id="ask-btn"')
    chips = html.find('class="ask-chips"')
    answer = html.find('id="ask-answer"')
    receipts = html.find('id="your-receipts"')
    assert 0 < ask_btn < chips < answer < receipts


def test_ask_uses_visible_seeds_not_the_api(client, fake_api) -> None:
    response = client.post(
        "/ask",
        data={
            "question": "How much did I spend per category?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    )
    assert response.status_code == 200
    assert fake_api.questions == []
    html = response.text
    assert "$21.20 on food" in html
    assert "$9.20 on drinks" in html
    assert "$16.10 on household" in html
    assert "$8.00 on snacks" in html
    assert "Across your 3 receipts" in html
    assert "DC demo data" not in html
    assert 'class="answer-q"' in html
    assert "How much did I spend per category?" in html
    assert 'data-scroll="ask-answer"' in html
    assert html.index("Ask a question") < html.index('class="answer-card"')
    assert 'id="flow-nav"' in html
    assert html.count("is-current") >= 1


def test_ask_moves_the_step_indicator_to_step_three(client) -> None:
    html = client.post(
        "/ask",
        data={
            "question": "How much did I spend on drinks in August?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    ).text
    nav = html.split('id="flow-nav"', 1)[1].split("</ol>", 1)[0]
    steps = nav.split("<li")
    assert "is-current" in steps[3]
    assert "is-current" not in steps[2]


def test_ask_drinks_in_august_uses_seed_corner_bakery(client, fake_api) -> None:
    response = client.post(
        "/ask",
        data={
            "question": "How much did I spend on drinks in August?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    )
    assert fake_api.questions == []
    html = response.text
    assert "$4.10 on drinks in August (Corner Bakery)." in html
    assert "Across your 3 receipts" in html
    assert "4.10 DC" not in html


def test_ingest_sample_one_click(client, fake_n8n, sample_id) -> None:
    response = client.post(
        "/ingest-sample",
        data={"start": "2026-07-01", "end": "2026-08-31"},
    )
    assert response.status_code == 200
    assert fake_n8n.calls == [sample_id]
    html = response.text
    assert MERCHANT in html
    assert "Extracted" not in html
    assert "✓ 10 items read in 0s" in html
    assert "Sample added ✓" in html
    assert 'id="ask-btn" class="btn"' in html
    assert 'id="sample-btn" class="btn-secondary"' in html
    assert "Reading your receipt…" in html
    assert "already in the corpus" not in html
    assert 'data-scroll="live-ingest"' in html
    assert html.count('class="receipt-heading"') == 0
    assert "cat-chip" in html
    assert "DC demo data" not in html
    assert "$25.00" in html
    assert "Just added" in html
    assert "is-added" in html
    assert "Lumen Pantry" in html
    assert "Remove live import" not in html
    assert "Examples and spending window" not in html
    assert "<abbr" not in html.split('id="review"', 1)[1].split("</table>", 1)[0]


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
    assert "min(1400px" in DEMO_CSS
    assert "min(720px" not in DEMO_CSS
    assert "font-size: 18px" in DEMO_CSS
    assert ".answer-slot" in DEMO_CSS
    assert ".just-added" in DEMO_CSS
    assert "#live-ingest" in DEMO_CSS
    assert "min-height: 168px" in DEMO_CSS
    assert ".reading-label" in DEMO_CSS
    assert "font-size: 20px" in DEMO_CSS
    assert "font-weight: 600" in DEMO_CSS
    assert ".receipts-total" in DEMO_CSS


def test_ask_after_extract_matches_visible_list(
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
    assert "$33.00 on food" in html
    assert "$13.60 on drinks" in html
    assert "$21.70 on household" in html
    assert "$11.20 on snacks" in html
    assert "Across your 4 receipts" in html
    assert "5.10 DC" not in html
    assert "DC demo data" not in html
    assert "Just added" in html


def test_ask_snacks_in_august_after_extract(client, fake_api, fake_n8n) -> None:
    client.post("/ingest-sample", data={"start": "2026-07-01", "end": "2026-08-31"})
    fake_api.questions.clear()
    html = client.post(
        "/ask",
        data={
            "question": "How much in snacks in August?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    ).text
    assert fake_api.questions == []
    assert "$6.70 on snacks in August" in html
    assert "Corner Bakery and Green Basket Market" in html
    assert "Across your 4 receipts" in html
    assert "16.70" not in html


def test_ask_this_receipt_snacks_after_extract(client, fake_api, fake_n8n) -> None:
    client.post("/ingest-sample", data={"start": "2026-07-01", "end": "2026-08-31"})
    html = client.post(
        "/ask",
        data={
            "question": "How much in snacks on this receipt?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    ).text
    assert fake_api.questions == []
    assert "$3.20 on snacks on this receipt (1 item: Butter croissants)." in html
    assert "From Green Basket Market, Aug 15" in html


def test_parse_posted_step_accepts_only_the_three_steps() -> None:
    assert parse_posted_step("3") == 3
    assert parse_posted_step(2) == 2
    assert parse_posted_step("0") is None
    assert parse_posted_step("") is None
    assert parse_posted_step(None) is None


def test_home_chips_skip_drinks_and_offer_an_item(client) -> None:
    html = client.get("/").text
    chips = html.split('aria-label="Suggested questions"', 1)[1].split("</div>", 1)[0]
    assert "drink" not in chips.lower()
    assert "Snacks in August" in chips
    assert "Most expensive item" in chips
    assert 'data-question="What was the most expensive item?"' in chips
    assert 'data-question="How much did I spend on snacks in August?"' in chips


def test_snacks_in_august_chip_has_a_nonzero_answer(client, fake_api) -> None:
    html = client.post(
        "/ask",
        data={
            "question": "How much did I spend on snacks in August?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    ).text
    assert fake_api.questions == []
    assert "You spent $3.50 on snacks in August (Corner Bakery)." in html
    assert "$0.00" not in html
    assert "couldn't match" not in html.lower()


def test_most_least_and_named_item_after_sample(client, fake_api, fake_n8n) -> None:
    client.post("/ingest-sample", data={"start": "2026-07-01", "end": "2026-08-31"})
    fake_api.questions.clear()
    most = client.post(
        "/ask",
        data={
            "question": "What was the most expensive item?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    ).text
    least = client.post(
        "/ask",
        data={
            "question": "What was the least expensive item?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    ).text
    named = client.post(
        "/ask",
        data={
            "question": "How much did the sourdough loaf cost?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    ).text
    assert fake_api.questions == []
    assert "The most expensive item was Sourdough loaf, $3.80." in most
    assert "couldn't match" not in most.lower()
    assert "The least expensive item was Bananas, $1.20." in least
    assert "Sourdough loaf cost $3.80" in named


def test_first_sample_extract_lands_on_review(client, fake_n8n) -> None:
    html = client.post(
        "/ingest-sample",
        data={"start": "2026-07-01", "end": "2026-08-31"},
    ).text
    assert _step_class(html, 1) == "is-done"
    assert _step_class(html, 2) == "is-current"
    assert _step_class(html, 3) == ""
    assert 'data-scroll="live-ingest"' in html


def test_extract_form_remembers_the_question_and_step(client) -> None:
    html = client.get("/").text
    assert "rememberVisitorPlace" in html
    assert "currentFlowStep" in html
    assert html.count('data-keep="question"') == 2
    assert html.count('data-keep="flow-step"') == 2


def test_second_sample_extract_keeps_question_and_step(client, fake_n8n) -> None:
    first = client.post(
        "/ingest-sample",
        data={"start": "2026-07-01", "end": "2026-08-31"},
    )
    assert _step_class(first.text, 2) == "is-current"
    html = client.post(
        "/ingest-sample",
        data={
            "start": "2026-07-01",
            "end": "2026-08-31",
            "question": "What was the most expensive item?",
            "flow_step": "3",
        },
    ).text
    assert len(fake_n8n.calls) == 2
    assert ">What was the most expensive item?</textarea>" in html
    assert _step_class(html, 1) == "is-done"
    assert _step_class(html, 2) == "is-done"
    assert _step_class(html, 3) == "is-current"
    assert 'data-scroll="live-ingest"' not in html


def test_second_extract_keeps_a_typed_question_on_the_review_step(
    client, fake_n8n
) -> None:
    client.post("/ingest-sample", data={"start": "2026-07-01", "end": "2026-08-31"})
    html = client.post(
        "/ingest-sample",
        data={
            "start": "2026-07-01",
            "end": "2026-08-31",
            "question": "bananas please",
            "flow_step": "2",
        },
    ).text
    assert ">bananas please</textarea>" in html
    assert _step_class(html, 2) == "is-current"
    assert _step_class(html, 3) == ""
