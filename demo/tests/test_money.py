"""Visitor-facing dollar formatting."""

from __future__ import annotations

from app.money import format_money, present_answer_text


def test_format_money_uses_a_dollar_sign() -> None:
    assert format_money(5.1) == "$5.10"


def test_present_answer_keeps_dollars_and_rewrites_dc() -> None:
    assert present_answer_text("You spent $5.10 on drinks.") == "You spent $5.10 on drinks."
    assert "5.10 DC" not in present_answer_text("You spent 5.10 DC on drinks.")
    assert "$5.10" in present_answer_text("You spent 5.10 DC on drinks.")


def test_present_answer_drops_raw_source_line() -> None:
    out = present_answer_text(
        "You spent $16.70 on snacks. Source: demo receipts from 2026-07-01 to 2026-08-31."
    )
    assert "Source:" not in out
    assert "2026-07-01" not in out
    assert "$16.70" in out


def test_present_answer_softens_empty_period_copy() -> None:
    out = present_answer_text("There is no recorded spending for that period.")
    assert "no recorded spending" not in out.lower()
    assert "drinks in August" in out
