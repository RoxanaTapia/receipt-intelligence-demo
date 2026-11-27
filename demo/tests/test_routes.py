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


def test_home_uses_the_brand_mark_and_the_sample_limit(client) -> None:
    html = client.get("/").text
    assert 'rel="icon"' in html
    assert "favicon.svg" in html
    assert 'sizes="32x32"' in html
    assert "favicon-32.png" in html
    assert 'rel="apple-touch-icon"' in html
    assert "apple-touch-icon.png" in html
    assert "fonts.googleapis.com" not in html
    assert "fonts.gstatic.com" not in html
    assert "Corner Studio is a fictional studio of five people." in html
    assert "sample data" in html
    assert "demo currency (DC)" in html
    icon = client.get("/demo-kit/favicon.svg")
    assert icon.status_code == 200
    assert b"#ff4d9a" in icon.content
    assert b"#e2186c" in icon.content
    assert b"#ff7a4a" in icon.content


def test_home_has_chips_and_extract_label(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "Run live ingest" not in html
    assert "Extract receipt" not in html
    assert "Read this receipt" in html
    assert "Reading this receipt…" in html
    assert "initDemo" in html
    assert "fillAskQuestion" in html
    assert "setReading" in html
    assert "markAskStep" in html
    for item in SUGGESTED_QUESTIONS:
        assert item["label"] in html
        assert f'data-question="{item["question"]}"' in html


def test_home_shows_the_august_cards_in_sample_currency(client) -> None:
    html = client.get("/").text
    assert "August receipts" in html
    assert "Green Basket Market" in html
    assert "15 Aug 2026" in html
    assert ">New<" in html
    assert "Lumen Pantry" in html
    assert "Harbor Home" in html
    assert "Corner Bakery" in html
    assert "18.90 DC" in html
    assert "14.20 DC" in html
    assert "21.40 DC" in html
    assert "Sample data" in html
    assert "Just added" not in html
    assert "Read this receipt" in html
    assert "Sample added" not in html
    assert "DC demo data" not in html
    assert "$" not in html
    assert "Examples and spending window" not in html
    assert "Remove live import" not in html
    receipts = html.find('id="live-ingest"')
    chips = html.find('class="ask-chips"')
    answer = html.find('id="ask-answer"')
    assert 0 < receipts < chips < answer
    assert 'id="your-receipts"' not in html


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
    assert "21.20 DC on food" in html
    assert "9.20 DC on drinks" in html
    assert "16.10 DC on household" in html
    assert "8.00 DC on snacks" in html
    assert "Across your 3 receipts" in html
    assert "DC demo data" not in html
    assert 'class="answer-q"' in html
    assert "How much did I spend per category?" in html
    assert 'data-scroll="ask-answer"' in html
    assert "Computed in Python from" in html
    assert "Answered in" in html
    assert html.index("Ask about August") < html.index('class="answer-card"')
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
    assert (
        "9.20 DC on drinks in August "
        "(Lumen Pantry, Harbor Home, and Corner Bakery)."
    ) in html
    assert "Across your 3 receipts" in html


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
    assert "10 items ·" in html
    assert "Sample added" not in html
    assert 'id="sample-btn"' not in html
    assert "Receipt read" in html
    assert ">Read<" in html
    assert html.count("Reading this receipt…") == 1
    assert "already in the corpus" not in html
    assert 'data-scroll="live-ingest"' in html
    assert html.count('class="receipt-heading"') == 0
    assert "cat-chip" in html
    assert "DC demo data" not in html
    assert "25.00 DC" in html
    assert "15 Aug 2026" in html
    review = html.split('id="review"', 1)[1].split("</section>", 1)[0]
    assert "2026-08-15" not in review
    assert "Just added" not in html
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
    assert "#9d174d" in DEMO_CSS
    assert "#3d4fd8" not in DEMO_CSS
    assert "Plus Jakarta Sans" in DEMO_CSS
    assert "Inter" not in DEMO_CSS
    assert "min(55rem" in DEMO_CSS
    assert "min(1400px" not in DEMO_CSS
    assert "min(720px" not in DEMO_CSS
    assert ".scan-line" in DEMO_CSS
    assert "text-overflow: clip" in DEMO_CSS
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
    assert "33.00 DC on food" in html
    assert "13.60 DC on drinks" in html
    assert "21.70 DC on household" in html
    assert "11.20 DC on snacks" in html
    assert "Across your 4 receipts" in html
    assert "5.10 DC" not in html
    assert "DC demo data" not in html
    assert "Receipt read" in html
    assert "Just added" not in html


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
    assert "11.20 DC on snacks in August" in html
    assert "Lumen Pantry, Corner Bakery, and Green Basket Market" in html
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
    assert "3.20 DC on snacks on this receipt (1 item: Butter croissants)." in html
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
    assert "Spend at Pine Market" in chips
    assert chips.count("ask-chip") == 4
    assert 'data-question="What was the most expensive item?"' in chips
    assert 'data-question="How much did I spend on snacks in August?"' in chips
    assert 'data-question="How much did I spend at Pine Market?"' in chips


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
    assert (
        "You spent 8.00 DC on snacks in August (Lumen Pantry and Corner Bakery)."
    ) in html
    assert "0.00 DC" not in html
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
    assert "The most expensive item was Sourdough loaf, 3.80 DC." in most
    assert "couldn't match" not in most.lower()
    assert "The least expensive item was Bananas, 1.20 DC." in least
    assert "Sourdough loaf cost 3.80 DC" in named


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
    # The sample is already saved for this browser, so the reader is not called again.
    assert len(fake_n8n.calls) == 1
    assert 'value="What was the most expensive item?"' in html
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
    assert 'value="bananas please"' in html
    assert _step_class(html, 2) == "is-current"
    assert _step_class(html, 3) == ""


def test_visitor_page_has_no_upload(client) -> None:
    html = client.get("/").text
    body = html.split("<body", 1)[1]
    assert 'type="file"' not in body
    assert "Or upload" not in body
    assert 'id="ingest-form"' not in body
    assert "sample-supermarket-receipt.pdf" not in html
    assert "Green Basket Market, 15 Aug" not in body
    assert "—" not in body


def test_operator_page_offers_the_human_sample_name(client) -> None:
    html = client.get("/", headers={"X-Ops-Ok": "1"}).text
    assert 'type="file"' in html
    assert "Or upload Green Basket Market, 15 Aug" in html
    assert "Download Green Basket Market, 15 Aug" in html
    assert "Extract receipt" in html
    assert "sample-supermarket-receipt.pdf" not in html
    assert 'data-operator="true"' in html


def test_visitor_post_cannot_open_the_upload(client) -> None:
    html = client.post(
        "/ingest",
        files={"pdf": ("sample-supermarket-receipt.pdf", b"%PDF", "application/pdf")},
        data={"start": "2026-07-01", "end": "2026-08-31"},
    ).text
    assert "Upload is for an operator session." in html
    body = html.split("<body", 1)[1]
    assert 'type="file"' not in body
