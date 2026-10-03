"""Which live receipt stays on screen until the visitor removes it."""

from __future__ import annotations

from typing import Any

from app.examples import ExampleReceipt


def _resolve_live_panel(
    live_receipt: dict[str, Any] | None,
    selected: ExampleReceipt | None,
    live_imports: list[ExampleReceipt],
) -> tuple[dict[str, Any] | None, ExampleReceipt | None]:
    """Pick the live panel receipt — stays until Remove clears live imports."""
    if live_receipt is not None:
        merchant = str(live_receipt.get("merchant") or "")
        receipt_date = str(live_receipt.get("date") or "")
        match = next(
            (
                item
                for item in live_imports
                if str(item.receipt.get("merchant") or "") == merchant
                and str(item.receipt.get("date") or "") == receipt_date
            ),
            None,
        )
        if match is None and selected is not None and selected.source == "live":
            match = selected
        if match is None and live_imports:
            match = live_imports[0]
        return live_receipt, match
    if selected is not None and selected.source == "live":
        return selected.receipt, selected
    if live_imports:
        return live_imports[0].receipt, live_imports[0]
    return None, None
