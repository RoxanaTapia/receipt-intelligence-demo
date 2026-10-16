"""Answers from the visible receipt catalog, matching the Your receipts list."""

from __future__ import annotations

import json
from pathlib import Path

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
        "Green Basket",
        "Green Basket Market",
    ]
    assert [row["just_added"] for row in rows] == [False, False, False, True]
    assert rows[-1]["date_label"] == "Aug 15"


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
        "(Green Basket and Green Basket Market)."
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
