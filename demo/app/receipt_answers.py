"""Answers from the receipts the visitor can see — seeds plus this session.

The companion API totals every JSON file on the shared volume, including
other visitors' leftover extracts. Numbers on this page come from the same
catalog as the Your receipts list so the two cannot disagree.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from app.money import format_money
from app.questions import _MONTH_NAME

CATEGORIES = ("snacks", "household", "drinks", "food")
_THIS_RECEIPT = re.compile(
    r"\bthis receipt\b|\bon this\b|\bthis one\b",
    re.IGNORECASE,
)
_DRINK_WORD = re.compile(r"\bdrinks?\b", re.IGNORECASE)


def short_date(value: str) -> str:
    """``2026-08-15`` → ``Aug 15`` — compact, no year."""
    parsed = _parse_date(value)
    if parsed is None:
        return value
    return f"{parsed.strftime('%b')} {parsed.day}"


def merchant_name(receipt: dict[str, Any]) -> str:
    return str(receipt.get("merchant") or "this receipt").strip() or "this receipt"


def receipt_list_rows(
    examples: list[Any],
    live_imports: list[Any],
) -> list[dict[str, Any]]:
    """Rows for the Your receipts list. Session live imports are just-added."""
    rows: list[dict[str, Any]] = []
    for item in examples:
        rows.append(_list_row(item.receipt, just_added=False))
    for item in live_imports:
        rows.append(_list_row(item.receipt, just_added=True))
    return rows


def catalog_payloads(examples: list[Any], live_imports: list[Any]) -> list[dict[str, Any]]:
    """Receipt dicts in the same order as the Your receipts list."""
    return [item.receipt for item in examples] + [item.receipt for item in live_imports]


def category_totals(receipt: dict[str, Any]) -> dict[str, float]:
    """Sum line prices per category on one receipt."""
    totals: dict[str, float] = {}
    for item in _lines(receipt):
        name = str(item.get("category") or "").strip().lower()
        if not name:
            continue
        totals[name] = round(totals.get(name, 0.0) + float(item.get("price") or 0), 2)
    return totals


def answer_visible_question(
    question: str,
    receipts: list[dict[str, Any]],
    current: dict[str, Any] | None = None,
) -> tuple[str, str] | None:
    """Return (answer, source) from the visible catalog, or ``None`` if unmatched."""
    if not receipts:
        return None
    scoped, single = _scope(question, receipts, current)
    month = _MONTH_NAME.search(question)
    month_name = month.group(0).title() if month else None
    in_month = (
        [receipt for receipt in scoped if _month_matches(receipt, month_name)]
        if month_name
        else scoped
    )

    if _is_per_category(question):
        return _per_category_answer(in_month, month_name), _source_line(
            in_month, receipts, single
        )

    category = _named_category(question)
    if category:
        return _category_answer(
            category, in_month, month_name, single
        ), _source_line(in_month, receipts, single)

    if _is_total_question(question):
        return _total_answer(in_month, month_name, single), _source_line(
            in_month, receipts, single
        )
    return None


def _list_row(receipt: dict[str, Any], *, just_added: bool) -> dict[str, Any]:
    raw_date = str(receipt.get("date") or "").strip()
    return {
        "merchant": merchant_name(receipt),
        "date": raw_date,
        "date_label": short_date(raw_date) if raw_date else "",
        "just_added": just_added,
    }


def _scope(
    question: str,
    receipts: list[dict[str, Any]],
    current: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], bool]:
    """Limit to the on-screen receipt only when the visitor asked for it."""
    if current is None:
        return receipts, False
    if _THIS_RECEIPT.search(question):
        return [current], True
    current_merchant = merchant_name(current).lower()
    if current_merchant and current_merchant in question.lower():
        return [current], True
    return receipts, False


def _source_line(
    used: list[dict[str, Any]],
    catalog: list[dict[str, Any]],
    single: bool,
) -> str:
    """Short card footer — one receipt, or the whole Your receipts count."""
    if single or len(catalog) <= 1:
        receipt = used[0] if used else (catalog[0] if catalog else {})
        label = merchant_name(receipt)
        raw_date = str(receipt.get("date") or "").strip()
        if raw_date:
            return f"From {label}, {short_date(raw_date)}"
        return f"From {label}"
    return f"Across your {len(catalog)} receipts"


def _per_category_answer(
    receipts: list[dict[str, Any]], month_name: str | None
) -> str:
    totals: dict[str, float] = {}
    for receipt in receipts:
        for name, amount in category_totals(receipt).items():
            totals[name] = round(totals.get(name, 0.0) + amount, 2)
    if not totals:
        when = f" in {month_name}" if month_name else ""
        return f"No categorized spending{when} on these receipts."
    order = [name for name in ("food", "drinks", "household", "snacks") if name in totals]
    extras = [name for name in sorted(totals) if name not in order]
    parts = [f"{format_money(totals[name])} on {name}" for name in [*order, *extras]]
    spent = _join_parts(parts)
    when = f" in {month_name}" if month_name else ""
    return f"You spent {spent}{when}."


def _category_answer(
    category: str,
    receipts: list[dict[str, Any]],
    month_name: str | None,
    single: bool,
) -> str:
    items: list[str] = []
    total = 0.0
    merchants: list[str] = []
    for receipt in receipts:
        lines = [
            item
            for item in _lines(receipt)
            if str(item.get("category") or "").strip().lower() == category
        ]
        if not lines:
            continue
        amount = round(sum(float(item.get("price") or 0) for item in lines), 2)
        total = round(total + amount, 2)
        merchants.append(merchant_name(receipt))
        items.extend(
            str(item.get("description") or "").strip() or "item" for item in lines
        )
    when = f" in {month_name}" if month_name else ""
    if total <= 0:
        if single:
            return f"No {category} on this receipt{when}."
        return f"No {category}{when} across your receipts."
    money = format_money(total)
    if single:
        return (
            f"You spent {money} on {category} on this receipt"
            f"{when} ({_item_phrase(items)})."
        )
    named = f" ({_join_names(merchants)})" if merchants else ""
    return f"You spent {money} on {category}{when}{named}."


def _total_answer(
    receipts: list[dict[str, Any]],
    month_name: str | None,
    single: bool,
) -> str:
    total = 0.0
    for receipt in receipts:
        total = round(total + _receipt_total(receipt), 2)
    money = format_money(total)
    when = f" in {month_name}" if month_name else ""
    if single:
        return f"You spent {money} on this receipt{when}."
    return f"You spent {money}{when}."


def _receipt_total(receipt: dict[str, Any]) -> float:
    if receipt.get("total") is not None:
        return float(receipt["total"])
    return round(sum(float(item.get("price") or 0) for item in _lines(receipt)), 2)


def _named_category(question: str) -> str | None:
    q = question.lower()
    if _DRINK_WORD.search(q):
        return "drinks"
    for name in CATEGORIES:
        if name == "drinks":
            continue
        if re.search(rf"\b{re.escape(name)}\b", q):
            return name
    return None


def _is_per_category(question: str) -> bool:
    q = question.lower()
    return "per category" in q or "by category" in q


def _is_total_question(question: str) -> bool:
    q = question.lower()
    return "how much" in q and _named_category(question) is None


def _month_matches(receipt: dict[str, Any], month_name: str) -> bool:
    parsed = _parse_date(str(receipt.get("date") or ""))
    return parsed is not None and parsed.strftime("%B") == month_name


def _lines(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    items = receipt.get("line_items") or []
    return [item for item in items if isinstance(item, dict)]


def _item_phrase(items: list[str]) -> str:
    names = [name for name in items if name]
    if not names:
        return "no line items"
    if len(names) == 1:
        return f"1 item: {names[0]}"
    return f"{len(names)} items: {_join_names(names)}"


def _join_names(names: list[str]) -> str:
    if len(names) <= 1:
        return names[0] if names else ""
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"


def _join_parts(parts: list[str]) -> str:
    if len(parts) <= 1:
        return parts[0] if parts else ""
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return f"{', '.join(parts[:-1])}, and {parts[-1]}"


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
