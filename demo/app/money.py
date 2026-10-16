"""Demo currency formatting for visitor-facing amounts."""

from __future__ import annotations

import re

# Neutral unit label — not EUR or USD (see issue #19).
DEMO_CURRENCY = "DC"

_DOLLAR_AMOUNT = re.compile(r"\$(\d+(?:\.\d{1,2})?)")
_EURO_AMOUNT = re.compile(r"€\s*(\d+(?:\.\d{1,2})?)")


def format_money(value: float | int | None) -> str:
    """Format an amount with the demo currency suffix, e.g. ``14.20 DC``."""
    if value is None:
        return f"— {DEMO_CURRENCY}"
    return f"{float(value):.2f} {DEMO_CURRENCY}"


def present_answer_text(
    text: str,
    *,
    window_start: str | None = None,
    window_end: str | None = None,
) -> str:
    """Rewrite API answer currency symbols and soften awkward refusal copy."""
    out = _DOLLAR_AMOUNT.sub(rf"\1 {DEMO_CURRENCY}", text)
    out = _EURO_AMOUNT.sub(rf"\1 {DEMO_CURRENCY}", out)
    lowered = out.lower()
    span = ""
    if window_start and window_end:
        span = f" Demo receipts cover {window_start} → {window_end}."
    if "couldn't map that" in lowered or "couldn't match that" in lowered:
        return (
            "I couldn't match that to a spending question for this demo."
            f"{span} "
            "Try a suggested question, or a category (food, drinks, snacks…) "
            "in a month that has data — for example, "
            "“How much did I spend on drinks in July?”"
        )
    if "no recorded spending" in lowered or "no spending recorded" in lowered:
        return (
            "I didn't find spending for that period."
            f"{span} "
            "Try a suggested question, or name a category and a month in that "
            "window — for example, “How much did I spend on drinks in July?”"
        )
    return out
