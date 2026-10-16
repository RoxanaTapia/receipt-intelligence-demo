"""Demo currency rewriting for visitor-facing answers."""

from __future__ import annotations

from app.money import format_money, present_answer_text


def test_format_money_uses_demo_currency() -> None:
    assert format_money(5.1) == "5.10 DC"


def test_present_answer_rewrites_dollar_amounts() -> None:
    out = present_answer_text("You spent $5.10 on drinks.")
    assert "$" not in out
    assert "5.10 DC" in out


def test_present_answer_softens_empty_period_copy() -> None:
    out = present_answer_text(
        "There is no recorded spending for that period.",
        window_start="2026-07-01",
        window_end="2026-08-31",
    )
    assert "no recorded spending" not in out.lower()
    assert "2026-07-01" in out
    assert "2026-08-31" in out
    assert "drinks in July" in out
