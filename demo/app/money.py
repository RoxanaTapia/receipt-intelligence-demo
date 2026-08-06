"""Demo currency formatting for visitor-facing amounts."""

from __future__ import annotations

import re

# Neutral unit label — not EUR or USD (see issue #19).
DEMO_CURRENCY = "DC"

_DOLLAR_AMOUNT = re.compile(r"\$(\d+(?:\.\d{1,2})?)")
_EURO_AMOUNT = re.compile(r"€\s*(\d+(?:\.\d{1,2})?)")
_MONTH_NAME = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\b",
    re.IGNORECASE,
)


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
    if "couldn't map that" in lowered or "couldn't match that" in lowered:
        span = ""
        if window_start and window_end:
            span = f" Demo receipts cover {window_start} → {window_end}."
        return (
            "I couldn't match that to a spending question for this demo."
            f"{span} "
            "Try a category (food, drinks, snacks…) in a month that has data — "
            "for example, “How much did I spend on drinks in July?”"
        )
    return out


def enrich_question_months(question: str, *, year: int) -> str:
    """Attach a year to the first bare month name so routing hits the demo corpus."""
    if re.search(r"\b20\d{2}\b", question):
        return question
    if not _MONTH_NAME.search(question):
        return question
    return _MONTH_NAME.sub(lambda match: f"{match.group(0)} {year}", question, count=1)
