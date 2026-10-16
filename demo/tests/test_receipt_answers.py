"""Answers scoped to the receipt on screen, not the shared corpus."""

from __future__ import annotations

from app.receipt_answers import answer_receipt_question, category_totals
from app.sample_receipt import receipt_payload


def test_green_basket_category_totals() -> None:
    totals = category_totals(receipt_payload())
    assert totals == {"food": 15.0, "drinks": 4.4, "household": 5.6}


def test_per_category_lists_this_receipt_only() -> None:
    text, source = answer_receipt_question(
        "How much did I spend per category?",
        receipt_payload(),
    )
    assert "15.00 DC" in text
    assert "4.40 DC" in text
    assert "5.60 DC" in text
    assert "25.00 DC" in text
    assert "July" not in text
    assert "snacks" not in text.lower()
    assert source == "Source: Green Basket Market, 2026-08-15."


def test_drinks_in_august_uses_receipt_date() -> None:
    text, source = answer_receipt_question(
        "How much did I spend on drinks in August?",
        receipt_payload(),
    )
    assert text == "You spent 4.40 DC on drinks in August."
    assert source == "Source: Green Basket Market, 2026-08-15."


def test_unknown_prompt_falls_through() -> None:
    assert answer_receipt_question("What is the tax rate?", receipt_payload()) is None
