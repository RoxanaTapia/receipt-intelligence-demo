"""Answers from the visible receipt catalog, matching the Your receipts list."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.live_panel import format_read_summary
from app.receipt_answers import (
    answer_visible_question,
    catalog_payloads,
    category_totals,
    receipt_list_rows,
    short_date,
)
from app.sample_receipt import receipt_payload

SEED_DIR = Path(__file__).resolve().parents[1] / "seed"


class _Item:
    def __init__(self, receipt: dict, file_name: str = "") -> None:
        self.receipt = receipt
        self.file_name = file_name


def _seed_receipts() -> list[dict]:
    receipts = []
    for path in sorted(SEED_DIR.glob("2026-*.json")):
        receipts.append(json.loads(path.read_text(encoding="utf-8")))
    return receipts


def test_read_summary_uses_count_and_elapsed() -> None:
    assert format_read_summary(10, 11.2) == "✓ 10 items read in 11s"
    assert format_read_summary(1, 0.2) == "✓ 1 item read in 0s"
    assert format_read_summary(10, None) == "✓ 10 items read"


def test_short_date_is_compact() -> None:
    assert short_date("2026-08-15") == "Aug 15"


def test_green_basket_category_totals() -> None:
    totals = category_totals(receipt_payload())
    assert totals == {"food": 11.8, "drinks": 4.4, "household": 5.6, "snacks": 3.2}


def test_list_rows_mark_live_imports_just_added() -> None:
    seeds = [_Item(row) for row in _seed_receipts()]
    live = [_Item(receipt_payload(), "live.json")]
    rows = receipt_list_rows(seeds, live)
    assert [row["merchant"] for row in rows] == [
        "Lumen Pantry",
        "Harbor Home",
        "Corner Bakery",
        "Green Basket Market",
    ]
    assert [row["just_added"] for row in rows] == [False, False, False, True]
    assert rows[-1]["date_label"] == "Aug 15"
    assert rows[-1]["total_label"] == "$25.00"
    assert rows[2]["merchant"] == "Corner Bakery"
    assert rows[2]["total_label"] == "$18.90"


def test_per_category_uses_every_visible_receipt() -> None:
    receipts = catalog_payloads(
        [_Item(row) for row in _seed_receipts()],
        [],
    )
    text, source = answer_visible_question(
        "How much did I spend per category?",
        receipts,
    )
    assert "$21.20 on food" in text
    assert "$9.20 on drinks" in text
    assert "$16.10 on household" in text
    assert "$8.00 on snacks" in text
    assert source == "Across your 3 receipts"


def test_august_snacks_names_the_receipts_in_the_list() -> None:
    receipts = _seed_receipts() + [receipt_payload()]
    text, source = answer_visible_question(
        "How much in snacks in August?",
        receipts,
        current=receipt_payload(),
    )
    assert text == (
        "You spent $6.70 on snacks in August "
        "(Corner Bakery and Green Basket Market)."
    )
    assert source == "Across your 4 receipts"
    assert "16.70" not in text


def test_this_receipt_snacks_uses_the_review_card() -> None:
    receipts = _seed_receipts() + [receipt_payload()]
    text, source = answer_visible_question(
        "How much in snacks on this receipt?",
        receipts,
        current=receipt_payload(),
    )
    assert text == (
        "You spent $3.20 on snacks on this receipt (1 item: Butter croissants)."
    )
    assert source == "From Green Basket Market, Aug 15"


def test_unknown_prompt_falls_through() -> None:
    assert answer_visible_question("What is the tax rate?", _seed_receipts()) is None


def test_most_expensive_item_on_the_open_sample() -> None:
    receipts = _seed_receipts() + [receipt_payload()]
    text, source = answer_visible_question(
        "What was the most expensive item?",
        receipts,
        current=receipt_payload(),
    )
    assert text == "The most expensive item was Sourdough loaf, $3.80."
    assert source == "From Green Basket Market, Aug 15"
    assert "Kitchen sponge" not in text


def test_least_expensive_item_on_the_open_sample() -> None:
    text, source = answer_visible_question(
        "What was the least expensive item?",
        _seed_receipts() + [receipt_payload()],
        current=receipt_payload(),
    )
    assert text == "The least expensive item was Bananas, $1.20."
    assert source == "From Green Basket Market, Aug 15"


def test_cheapest_matches_the_least_expensive_item() -> None:
    text, _source = answer_visible_question(
        "Which item was the cheapest?",
        [receipt_payload()],
        current=receipt_payload(),
    )
    assert "Bananas, $1.20" in text


def test_most_expensive_across_seeds_when_nothing_is_open() -> None:
    text, source = answer_visible_question(
        "What was the most expensive item?",
        _seed_receipts(),
    )
    assert text == "The most expensive item was Kitchen sponge set, $6.00."
    assert source == "Across your 3 receipts"


def test_most_expensive_in_a_month_uses_every_receipt_that_month() -> None:
    text, _source = answer_visible_question(
        "What was the most expensive item in August?",
        _seed_receipts() + [receipt_payload()],
        current=receipt_payload(),
    )
    assert text == "The most expensive item was Yogurt cups, $5.60."


def test_most_expensive_across_all_receipts_when_asked() -> None:
    text, _source = answer_visible_question(
        "What was the most expensive item across all receipts?",
        _seed_receipts() + [receipt_payload()],
        current=receipt_payload(),
    )
    assert text == "The most expensive item was Kitchen sponge set, $6.00."


def test_tied_most_expensive_items_are_both_named() -> None:
    receipt = {
        "merchant": "Test Market",
        "date": "2026-08-02",
        "line_items": [
            {"description": "Pears", "price": 4, "category": "food"},
            {"description": "Plums", "price": 4, "category": "food"},
            {"description": "Tape", "price": 1, "category": "household"},
        ],
    }
    text, _source = answer_visible_question(
        "What was the most expensive item?",
        [receipt],
        current=receipt,
    )
    assert text == "The most expensive items were Pears, $4.00 and Plums, $4.00."


def test_named_item_cost_on_the_sample() -> None:
    text, source = answer_visible_question(
        "How much did the sourdough loaf cost?",
        [receipt_payload()],
        current=receipt_payload(),
    )
    assert text == "Sourdough loaf cost $3.80."
    assert source == "From Green Basket Market, Aug 15"


def test_named_item_on_this_receipt_stays_on_that_receipt() -> None:
    text, source = answer_visible_question(
        "How much did the sourdough loaf cost on this receipt?",
        _seed_receipts() + [receipt_payload()],
        current=receipt_payload(),
    )
    assert text == "Sourdough loaf cost $3.80."
    assert source == "From Green Basket Market, Aug 15"


def test_named_item_lists_each_price() -> None:
    text, _source = answer_visible_question(
        "How much did sparkling water cost?",
        _seed_receipts() + [receipt_payload()],
        current=receipt_payload(),
    )
    assert text == (
        "Sparkling water cost $2.70 at Harbor Home and $1.50 at Green Basket Market."
    )


def test_named_item_matches_without_a_pack_size() -> None:
    text, _source = answer_visible_question(
        "How much did the whole milk cost?",
        [receipt_payload()],
        current=receipt_payload(),
    )
    assert text == "Whole milk 1L cost $1.80."


def test_unknown_item_does_not_become_the_total() -> None:
    text, _source = answer_visible_question(
        "How much did the caviar cost?",
        _seed_receipts(),
    )
    assert text == "I couldn't find that item on these receipts."
    assert "54.50" not in text


@pytest.mark.parametrize(
    "question",
    [
        "How much was my total in August?",
        "How much did we pay in August?",
        "How much have I paid in August?",
        "How much did I spend in August?",
    ],
)
def test_spend_wording_stays_a_total(question: str) -> None:
    text, _source = answer_visible_question(question, _seed_receipts())
    assert text == "You spent $18.90 in August."
    assert "couldn't find that item" not in text.lower()


@pytest.mark.parametrize(
    "question",
    [
        "How much did I pay for the sourdough loaf?",
        "What did I pay for the sourdough loaf?",
        "How much did I spend on the sourdough loaf?",
    ],
)
def test_pay_or_spend_for_a_named_item(question: str) -> None:
    text, _source = answer_visible_question(question, _seed_receipts())
    assert text == "Sourdough loaf cost $3.80."


def test_spend_total_is_not_an_item_lookup() -> None:
    text, source = answer_visible_question("How much did I spend?", _seed_receipts())
    assert text == "You spent $54.50."
    assert source == "Across your 3 receipts"


def test_how_much_for_a_category_stays_a_category_total() -> None:
    text, _source = answer_visible_question(
        "How much for snacks in August?",
        _seed_receipts(),
    )
    assert text == "You spent $3.50 on snacks in August (Corner Bakery)."
