"""Visitor-facing money: a plain dollar sign, no demo-currency jargon."""

from __future__ import annotations

import re

DEMO_CURRENCY = "$"

_DC_AMOUNT = re.compile(r"(\d+(?:\.\d{1,2})?)\s*DC\b")
_EURO_AMOUNT = re.compile(r"€\s*(\d+(?:\.\d{1,2})?)")
_SOURCE_TAIL = re.compile(
    r"\s*Source:\s*.+$",
    re.IGNORECASE | re.DOTALL,
)


def format_money(value: float | int | None) -> str:
    """Format an amount the way the review table shows it, e.g. ``$3.20``."""
    if value is None:
        return "—"
    return f"${float(value):.2f}"


def present_answer_text(text: str) -> str:
    """Rewrite leftover API currency labels and drop a raw Source: tail."""
    out = _DC_AMOUNT.sub(r"$\1", text)
    out = _EURO_AMOUNT.sub(r"$\1", out)
    out = _SOURCE_TAIL.sub("", out).strip()
    lowered = out.lower()
    if "couldn't map that" in lowered or "couldn't match that" in lowered:
        return (
            "I couldn't match that to a spending question. "
            "Try a suggested question, or a category (food, drinks, snacks…)."
        )
    if "no recorded spending" in lowered or "no spending recorded" in lowered:
        return (
            "I didn't find spending for that. "
            "Try a suggested question, or name a category — for example, "
            "“How much did I spend on drinks in August?”"
        )
    return out
