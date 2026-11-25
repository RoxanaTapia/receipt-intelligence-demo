"""Visitor-facing money: demo currency (DC), labelled as sample data.

DC is not a real currency. Amounts on the page stay in this unit so they
match the Corner Studio case and the printed sample receipt.
"""

from __future__ import annotations

import re

DEMO_CURRENCY = "DC"

_SYMBOL_AMOUNT = re.compile(r"(?:\$|€)\s*(\d+(?:\.\d{1,2})?)")
_DC_AMOUNT = re.compile(r"(\d+(?:\.\d{1,2})?)\s*DC\b")
_SOURCE_TAIL = re.compile(
    r"\s*Source:\s*.+$",
    re.IGNORECASE | re.DOTALL,
)


def format_money(value: float | int | None) -> str:
    """Format an amount the way the case study shows it, e.g. ``3.20 DC``."""
    if value is None:
        return "n/a"
    return f"{float(value):.2f} DC"


def _as_dc(match: re.Match[str]) -> str:
    return f"{float(match.group(1)):.2f} DC"


def present_answer_text(text: str) -> str:
    """Rewrite leftover currency symbols into DC and drop a raw Source: tail."""
    out = _SYMBOL_AMOUNT.sub(_as_dc, text)
    out = _DC_AMOUNT.sub(_as_dc, out)
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
            "Try a suggested question, or name a category. For example, "
            "“How much did I spend on drinks in August?”"
        )
    return out
