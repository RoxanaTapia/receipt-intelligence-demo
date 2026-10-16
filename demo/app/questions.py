"""Visitor Q&A helpers: suggested prompts and demo-window routing."""

from __future__ import annotations

import re
from datetime import date

# Category + month questions the companion API can answer today.
SUGGESTED_QUESTIONS = (
    "How much did I spend on drinks in July?",
    "How much did I spend on food in August?",
    "How much did I spend on household in July?",
)

_MONTH_NAME = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\b",
    re.IGNORECASE,
)
_ISO_DATE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
_YEAR = re.compile(r"\b20\d{2}\b")
_RELATIVE_TIME = re.compile(
    r"\b(today|yesterday|this week|last week|this month|last month|"
    r"this year|last year|this quarter)\b",
    re.IGNORECASE,
)


def enrich_question_months(question: str, *, year: int) -> str:
    """Attach a year to the first bare month name so routing hits the demo corpus."""
    if re.search(r"\b20\d{2}\b", question):
        return question
    if not _MONTH_NAME.search(question):
        return question
    return _MONTH_NAME.sub(lambda match: f"{match.group(0)} {year}", question, count=1)


def question_has_time_window(question: str) -> bool:
    """True when the visitor already named a date, month, year, or relative period."""
    return bool(
        _ISO_DATE.search(question)
        or _YEAR.search(question)
        or _MONTH_NAME.search(question)
        or _RELATIVE_TIME.search(question)
    )


def apply_demo_window(question: str, window_start: str, window_end: str) -> str:
    """Pin undated questions to the spending filter so the API does not use today."""
    if question_has_time_window(question):
        return question
    phrase = f"from {window_start} to {window_end}"
    stripped = question.strip()
    suffix = ""
    if stripped.endswith("?"):
        stripped = stripped[:-1].rstrip()
        suffix = "?"
    return f"{stripped} {phrase}{suffix}"


def prepare_question(question: str, *, window_start: str, window_end: str) -> str:
    """Rewrite a visitor question so Q&A lands in the visible demo window.

    The companion API decides the aggregation span (often ``date.today()`` when
    no date is in the text). Analytics on this page already uses ``window_start``
    / ``window_end``. We put that same span in the question so undated prompts
    such as “How much did I spend per category?” match the totals on screen.
    """
    try:
        year = date.fromisoformat(window_start).year
    except ValueError:
        year = int(window_start[:4]) if len(window_start) >= 4 else 2026
    with_year = enrich_question_months(question, year=year)
    return apply_demo_window(with_year, window_start, window_end)
