"""Camera fixes: one August period, final figures, an honest miss, done labels."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.receipt_answers import answer_visible_question, case_view
from app.sample_receipt import receipt_payload

_SEED_DIR = Path(__file__).resolve().parents[1] / "seed"


def _seed_receipts() -> list[dict]:
    receipts = []
    for path in sorted(_SEED_DIR.glob("2026-*.json")):
        receipts.append(json.loads(path.read_text(encoding="utf-8")))
    return receipts

_MONEY = re.compile(r'class="num">([0-9]+\.[0-9]{2}) DC')
_WINDOW = {"start": "2026-07-01", "end": "2026-08-31"}


def _ask(client, question: str) -> str:
    return client.post("/ask", data={"question": question, **_WINDOW}).text


def _card(html: str) -> str:
    return html.split('class="answer-card"', 1)[1].split("</section>", 1)[0]


def _category_amount(card: str, name: str) -> float:
    chunk = card.split(f'class="cat-name">{name}', 1)[1]
    match = _MONEY.search(chunk)
    assert match is not None
    return float(match.group(1))


def _headline(card: str) -> float:
    match = _MONEY.search(card)
    assert match is not None
    return float(match.group(1))


def test_seed_receipts_are_dated_in_august() -> None:
    dates = [receipt["date"] for receipt in _seed_receipts()]
    assert dates == ["2026-08-01", "2026-08-12", "2026-08-20"]
    assert all(date.startswith("2026-08-") for date in dates)


def test_august_panels_use_the_same_totals() -> None:
    seeds = _seed_receipts()
    per = case_view("How much did I spend per category?", seeds)
    snacks = case_view("How much did I spend on snacks in August?", seeds)
    assert per is not None and snacks is not None
    assert per.amount == round(sum(row["amount"] for row in per.categories), 2)
    snack_row = next(row for row in per.categories if row["name"] == "snacks")
    assert snacks.amount == snack_row["amount"] == 8.00
    assert per.cited_note == "Top item in each category."

    visible = seeds + [receipt_payload()]
    per_all = case_view("How much did I spend per category?", visible)
    snacks_all = case_view("How much did I spend on snacks in August?", visible)
    assert per_all is not None and snacks_all is not None
    assert per_all.amount == round(sum(row["amount"] for row in per_all.categories), 2)
    assert per_all.amount == 79.50
    snack_all = next(row for row in per_all.categories if row["name"] == "snacks")
    assert snacks_all.amount == snack_all["amount"] == 11.20


def test_a_later_month_stays_out_of_august() -> None:
    extra = {
        "merchant": "North Market",
        "date": "2026-09-02",
        "total": 9.0,
        "line_items": [
            {"description": "Gold tin", "price": 9.0, "category": "snacks"}
        ],
    }
    text, _source = answer_visible_question(
        "How much did I spend on snacks in August?",
        _seed_receipts() + [extra],
    )
    assert text is not None
    assert "9.00" not in text
    assert "North Market" not in text
    assert "8.00 DC" in text


def test_a_shop_on_the_receipts_keeps_its_own_total() -> None:
    text, source = answer_visible_question(
        "How much did I spend at Harbor Home?",
        _seed_receipts(),
    )
    assert text == "You spent 21.40 DC on this receipt."
    assert source == "From Harbor Home, Aug 20"
    assert "54.50" not in text
    assert "not in the receipts" not in text


def test_home_receipts_are_all_in_august(client) -> None:
    html = client.get("/").text
    panel = html.split('id="live-ingest"', 1)[1].split("</section>", 1)[0]
    assert "Jul" not in panel
    assert "12 Aug 2026" in panel
    assert "20 Aug 2026" in panel
    assert "1 Aug 2026" in panel
    assert "15 Aug 2026" in panel


def test_on_screen_totals_agree_for_august(client, fake_api) -> None:
    per = _card(_ask(client, "How much did I spend per category?"))
    snacks = _card(_ask(client, "How much did I spend on snacks in August?"))
    assert fake_api.questions == []
    assert _headline(per) == round(
        _category_amount(per, "food")
        + _category_amount(per, "drinks")
        + _category_amount(per, "household")
        + _category_amount(per, "snacks"),
        2,
    )
    assert _headline(per) == 54.50
    assert _headline(snacks) == _category_amount(per, "snacks") == 8.00
    assert "Top item in each category." in per
    for name in ("Yogurt cups", "Herbal tea", "Kitchen sponge set", "Mixed nuts"):
        assert name in per


def test_amounts_are_final_with_no_count_up(client) -> None:
    html = _ask(client, "How much did I spend per category?")
    assert "data-count-money" not in html
    assert "countMoney" not in html
    assert "54.50 DC" in html
    assert "prefers-reduced-motion" in html
    assert html.count("Computed in Python") == 1


def test_fourth_preset_says_the_shop_is_not_in_the_receipts(client, fake_api) -> None:
    home = client.get("/").text
    chips = home.split('aria-label="Suggested questions"', 1)[1].split("</div>", 1)[0]
    assert chips.count("ask-chip") == 4
    assert "Spend at Pine Market" in chips
    html = _ask(client, "How much did I spend at Pine Market?")
    assert fake_api.questions == []
    card = _card(html)
    answer = card.split('class="answer-a"', 1)[1].split("</p>", 1)[0]
    assert "Pine Market is not in the receipts." in answer
    assert "DC" not in answer
    assert not any(char.isdigit() for char in answer)


def test_reading_phrase_is_shown_once(client) -> None:
    html = client.get("/").text
    assert html.count("Reading this receipt…") == 1
    assert "Read this receipt" in html


def test_read_card_uses_done_labels(client, fake_n8n) -> None:
    html = client.post("/ingest-sample", data=_WINDOW).text
    assert fake_n8n.calls
    card = html.split('id="live-ingest"', 1)[1].split("</section>", 1)[0]
    review = html.split('id="review"', 1)[1].split("<table>", 1)[0]
    assert "Just added" not in card
    assert "Read this receipt" not in card
    assert "Receipt read" in card
    assert ">Read<" in card
    assert "still a label" not in card
    assert "Receipt read" in review
    assert "Read this receipt" not in review
    assert html.count("Reading this receipt…") == 1
    assert html.count("Computed in Python") == 0
