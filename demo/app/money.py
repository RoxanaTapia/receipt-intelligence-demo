"""Demo currency formatting for visitor-facing amounts."""

from __future__ import annotations

# Neutral unit label — not EUR or USD (see issue #19).
DEMO_CURRENCY = "DC"


def format_money(value: float | int | None) -> str:
    """Format an amount with the demo currency suffix, e.g. ``14.20 DC``."""
    if value is None:
        return f"— {DEMO_CURRENCY}"
    return f"{float(value):.2f} {DEMO_CURRENCY}"
