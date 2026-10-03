"""Spending contrast for the demo window: category shares, seed baseline, before and after."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _category_share_map(summary: dict[str, Any] | None) -> dict[str, dict[str, float]]:
    """Map category → {spend, pct} from a summary payload."""
    if not summary:
        return {}
    rows = summary.get("by_category") or []
    out: dict[str, dict[str, float]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("category") or "")
        if not name:
            continue
        out[name] = {
            "spend": float(row.get("total_spend") or 0),
            "pct": float(row.get("percentage") or 0),
        }
    return out


def _seed_baseline_spend(seed_dir: Path, start: str, end: str) -> float:
    """Sum line prices on seed fixtures inside the selected window (for UX contrast)."""
    total = 0.0
    for path in sorted(seed_dir.glob("2026-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        receipt_date = str(data.get("date") or "")
        if receipt_date < start or receipt_date > end:
            continue
        for item in data.get("line_items") or []:
            if isinstance(item, dict):
                total += float(item.get("price") or 0)
    return round(total, 2)


def _outside_window(receipt: dict[str, Any] | None, start: str, end: str) -> bool:
    """True when a live receipt date falls outside the spending filter."""
    if not receipt:
        return False
    receipt_date = str(receipt.get("date") or "")
    if not receipt_date:
        return False
    return receipt_date < start or receipt_date > end


def _spending_contrast(
    *,
    summary: dict[str, Any] | None,
    summary_before: dict[str, Any] | None,
    start: str,
    end: str,
    panel_receipt: dict[str, Any] | None,
    seed_dir: Path,
) -> dict[str, Any]:
    """Before/after totals and category shares the spending panel renders."""
    spend_before = (
        float(summary_before["total_spend"])
        if summary_before and summary_before.get("total_spend") is not None
        else None
    )
    spend_after = (
        float(summary["total_spend"])
        if summary and summary.get("total_spend") is not None
        else None
    )
    spend_delta = None
    if spend_before is not None and spend_after is not None:
        spend_delta = round(spend_after - spend_before, 2)
    return {
        "before_map": _category_share_map(summary_before),
        "spend_before": spend_before,
        "spend_after": spend_after,
        "spend_delta": spend_delta,
        "seed_baseline": _seed_baseline_spend(seed_dir, start, end),
        "live_outside_window": _outside_window(panel_receipt, start, end),
    }
