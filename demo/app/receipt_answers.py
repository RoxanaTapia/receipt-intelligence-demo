"""Answers scoped to the receipt on screen — not the shared corpus.

The companion API aggregates every JSON file on the receipts volume. This demo
answers the storyboard chips from the session's live receipt so the numbers
match the review card. Corpus-wide Q&A still needs the API (see PR notes).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.money import format_money
from app.questions import _MONTH_NAME


def category_totals(receipt: dict[str, Any]) -> dict[str, float]:
    """Sum line prices per category on one receipt."""
    totals: dict[str, float] = {}
    for item in receipt.get("line_items") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("category") or "").strip().lower()
        if not name:
            continue
        totals[name] = round(totals.get(name, 0.0) + float(item.get("price") or 0), 2)
    return totals


def receipt_source_line(receipt: dict[str, Any]) -> str:
    """Where the on-screen numbers came from (no extra DC note)."""
    merchant = str(receipt.get("merchant") or "this receipt").strip() or "this receipt"
    receipt_date = str(receipt.get("date") or "").strip()
    if receipt_date:
        return f"Source: {merchant}, {receipt_date}."
    return f"Source: {merchant}."


def answer_receipt_question(
    question: str, receipt: dict[str, Any]
) -> tuple[str, str] | None:
    """Return (answer, source) for chips that this receipt can answer.

    ``None`` means fall back to the companion API (corpus-wide).
    """
    q = question.lower()
    totals = category_totals(receipt)
    source = receipt_source_line(receipt)
    receipt_date = _parse_date(str(receipt.get("date") or ""))

    if "per category" in q or "by category" in q:
        if not totals:
            return "This receipt has no categorized line items.", source
        parts = [
            f"{name} {format_money(amount)}"
            for name, amount in sorted(totals.items())
        ]
        total = round(sum(totals.values()), 2)
        text = f"{', '.join(parts)} ({format_money(total)} total)."
        return text[0].upper() + text[1:], source

    month = _MONTH_NAME.search(question)
    if "drink" in q and month:
        wanted = month.group(0).title()
        spent = totals.get("drinks", 0.0)
        if receipt_date is None:
            return None
        if receipt_date.strftime("%B") != wanted:
            return (
                f"This receipt is not from {wanted} — no drinks in {wanted} on it.",
                source,
            )
        if spent <= 0:
            return f"No drinks on this receipt in {wanted}.", source
        return f"You spent {format_money(spent)} on drinks in {wanted}.", source

    return None


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
