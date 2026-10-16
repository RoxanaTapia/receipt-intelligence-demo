"""Canonical Green Basket Market sample — PDF, fake ingest, and allowlist share this.

n8n still maps each line to the demo taxonomy (food / drinks / household).
Department labels on the PDF (Produce, Dairy, …) are for the visitor, not the JSON.
"""

from __future__ import annotations

from typing import Any

MERCHANT = "Green Basket Market"
DATE = "2026-08-15"
ADDRESS_LINES = ("14 Harbor Lane", "Demo City")
CURRENCY = "DC"

# Everyday supermarket lines. Prices sum to a round 25.00 DC.
ITEMS: tuple[dict[str, Any], ...] = (
    {
        "description": "Bananas",
        "dept": "Produce",
        "quantity": 1,
        "price": 1.20,
        "category": "food",
    },
    {
        "description": "Baby spinach",
        "dept": "Produce",
        "quantity": 1,
        "price": 2.40,
        "category": "food",
    },
    {
        "description": "Whole milk 1L",
        "dept": "Dairy",
        "quantity": 1,
        "price": 1.80,
        "category": "food",
    },
    {
        "description": "Greek yogurt",
        "dept": "Dairy",
        "quantity": 1,
        "price": 2.60,
        "category": "food",
    },
    {
        "description": "Orange juice",
        "dept": "Drinks",
        "quantity": 1,
        "price": 2.90,
        "category": "drinks",
    },
    {
        "description": "Sparkling water",
        "dept": "Drinks",
        "quantity": 2,
        "price": 1.50,
        "category": "drinks",
    },
    {
        "description": "Sourdough loaf",
        "dept": "Bakery",
        "quantity": 1,
        "price": 3.80,
        "category": "food",
    },
    {
        "description": "Butter croissants",
        "dept": "Bakery",
        "quantity": 2,
        "price": 3.20,
        "category": "food",
    },
    {
        "description": "Dish soap",
        "dept": "Household",
        "quantity": 1,
        "price": 2.50,
        "category": "household",
    },
    {
        "description": "Paper towels",
        "dept": "Household",
        "quantity": 1,
        "price": 3.10,
        "category": "household",
    },
)


def receipt_total() -> float:
    """Sum of line prices — the one total printed on the sample."""
    return round(sum(float(item["price"]) for item in ITEMS), 2)


def receipt_payload() -> dict[str, Any]:
    """JSON body n8n would persist after extracting this PDF."""
    return {
        "date": DATE,
        "merchant": MERCHANT,
        "total": receipt_total(),
        "line_items": [
            {
                "description": item["description"],
                "quantity": item["quantity"],
                "price": item["price"],
                "category": item["category"],
            }
            for item in ITEMS
        ],
    }
