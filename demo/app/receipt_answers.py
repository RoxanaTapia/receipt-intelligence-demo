"""Answers from the receipts the visitor can see — seeds plus this session.

The companion API totals every JSON file on the shared volume, including
other visitors' leftover extracts. Numbers on this page come from the same
catalog as the Your receipts list so the two cannot disagree.

Item questions (most or least expensive, or the price of a named line) use
those same line items. A bare "most expensive item" follows the receipt on
the review card when one is open, which is the sample just extracted.
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
_MOST_ITEM = re.compile(
    r"\b(?:most expensive|highest priced|highest price|priciest|costliest)\b",
    re.IGNORECASE,
)
_LEAST_ITEM = re.compile(
    r"\b(?:least expensive|cheapest|lowest priced|lowest price)\b",
    re.IGNORECASE,
)
_ACROSS_RECEIPTS = re.compile(
    r"\b(?:across|all|every|each)\b(?:\s+\w+){0,4}\s+receipts?\b",
    re.IGNORECASE,
)
# "How much did the sourdough loaf cost?" — not "how much did I spend".
_ITEM_PRICE = re.compile(
    r"\b(?:"
    r"how much (?:did|does|do|was|is|were|for) (?:the |a |an )?"
    r"|price of (?:the |a |an )?"
    r"|cost of (?:the |a |an )?"
    r"|paid for (?:the |a |an )?"
    r"|what did .+? cost"
    r")",
    re.IGNORECASE,
)
_SPEND_TOTAL = re.compile(r"\bhow much did (?:i|we) spend\b", re.IGNORECASE)


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

    rank = _item_rank(question)
    if rank:
        pool, ranked_single = _item_pool(
            question, in_month, current, single, month_name
        )
        category = _named_category(question)
        records = _line_records(pool)
        if category:
            records = [
                record for record in records if record["category"] == category
            ]
        return (
            _ranked_item_answer(
                records,
                rank=rank,
                month_name=month_name,
                single=ranked_single,
                category=category,
            ),
            _source_line(pool, receipts, ranked_single),
        )

    if _is_item_price_question(question):
        matches = _matching_items(question, in_month)
        if matches:
            return _named_item_answer(matches), _named_item_source(
                matches, in_month, receipts, single
            )
        # "How much for snacks?" names a category, not a line. Keep going.
        if _named_category(question) is None:
            return (
                "I couldn't find that item on these receipts.",
                _source_line(in_month, receipts, single),
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
    total = _receipt_total(receipt)
    return {
        "merchant": merchant_name(receipt),
        "date": raw_date,
        "date_label": short_date(raw_date) if raw_date else "",
        "total": total,
        "total_label": format_money(total),
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


def _item_rank(question: str) -> str | None:
    """``most`` or ``least`` when the visitor is asking about a line item."""
    most = _MOST_ITEM.search(question)
    least = _LEAST_ITEM.search(question)
    if most and least:
        return "most" if most.start() < least.start() else "least"
    if most:
        return "most"
    if least:
        return "least"
    return None


def _item_pool(
    question: str,
    in_month: list[dict[str, Any]],
    current: dict[str, Any] | None,
    single: bool,
    month_name: str | None,
) -> tuple[list[dict[str, Any]], bool]:
    """Receipts for a most/least question.

    The open review card is the sample the visitor just extracted, so a bare
    "most expensive item" answers from that receipt. A month name, an explicit
    "this receipt", or "across all receipts" keeps the wider set.
    """
    widened = bool(month_name) or _ACROSS_RECEIPTS.search(question) is not None
    if single or widened or current is None:
        return in_month, single
    return [current], True


def _is_item_price_question(question: str) -> bool:
    if _SPEND_TOTAL.search(question):
        return False
    return _ITEM_PRICE.search(question) is not None


def _line_records(receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for receipt in receipts:
        for item in _lines(receipt):
            description = str(item.get("description") or "").strip()
            if not description:
                continue
            try:
                price = round(float(item.get("price")), 2)
            except (TypeError, ValueError):
                continue
            records.append(
                {
                    "description": description,
                    "price": price,
                    "category": str(item.get("category") or "").strip().lower(),
                    "merchant": merchant_name(receipt),
                    "receipt": receipt,
                }
            )
    return records


def _ranked_item_answer(
    records: list[dict[str, Any]],
    *,
    rank: str,
    month_name: str | None,
    single: bool,
    category: str | None,
) -> str:
    if not records:
        when = f" in {month_name}" if month_name else ""
        where = "on this receipt" if single else "on these receipts"
        what = f"{category} items" if category else "line items"
        return f"No {what}{when} {where}."
    target = max(record["price"] for record in records)
    if rank == "least":
        target = min(record["price"] for record in records)
    winners: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        if record["price"] != target:
            continue
        key = record["description"].casefold()
        if key in seen:
            continue
        seen.add(key)
        winners.append(record)
    label = "most expensive" if rank == "most" else "least expensive"
    if len(winners) == 1:
        winner = winners[0]
        return (
            f"The {label} item was {winner['description']}, "
            f"{format_money(winner['price'])}."
        )
    parts = [
        f"{winner['description']}, {format_money(winner['price'])}"
        for winner in winners
    ]
    return f"The {label} items were {_join_parts(parts)}."


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _needles(description: str) -> list[str]:
    """Full name, plus the name without a trailing pack size (``1L``)."""
    full = _norm(description)
    if not full:
        return []
    trimmed = re.sub(r"\s+\d+[a-z]*$", "", full).strip()
    if trimmed and trimmed != full:
        return [full, trimmed]
    return [full]


def _matching_items(
    question: str, receipts: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Line items whose description appears in the question. Longest name wins."""
    norm_q = f" {_norm(question)} "
    records = _line_records(receipts)
    best: tuple[int, str] | None = None
    for record in records:
        for needle in _needles(record["description"]):
            if len(needle) < 3:
                continue
            if f" {needle} " in norm_q and (best is None or len(needle) > best[0]):
                best = (len(needle), _norm(record["description"]))
    if best is None:
        return []
    return [record for record in records if _norm(record["description"]) == best[1]]


def _named_item_answer(matches: list[dict[str, Any]]) -> str:
    name = str(matches[0]["description"])
    prices = {match["price"] for match in matches}
    merchants: list[str] = []
    seen_merchants: set[str] = set()
    for match in matches:
        merchant = str(match["merchant"])
        if merchant in seen_merchants:
            continue
        seen_merchants.add(merchant)
        merchants.append(merchant)
    if len(prices) == 1:
        money = format_money(matches[0]["price"])
        if len(merchants) == 1:
            return f"{name} cost {money}."
        return f"{name} cost {money} ({_join_names(merchants)})."
    parts: list[str] = []
    seen_prices: set[tuple[str, float]] = set()
    for match in matches:
        key = (str(match["merchant"]), float(match["price"]))
        if key in seen_prices:
            continue
        seen_prices.add(key)
        parts.append(f"{format_money(match['price'])} at {match['merchant']}")
    return f"{name} cost {_join_parts(parts)}."


def _named_item_source(
    matches: list[dict[str, Any]],
    used: list[dict[str, Any]],
    catalog: list[dict[str, Any]],
    single: bool,
) -> str:
    merchants = {match["merchant"] for match in matches}
    if single or len(merchants) == 1:
        return _source_line([matches[0]["receipt"]], catalog, True)
    return _source_line(used, catalog, False)


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
