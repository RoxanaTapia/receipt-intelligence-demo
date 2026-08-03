"""Load visitor-facing example receipts from seed JSON on disk."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExampleReceipt:
    """One pickable demo receipt plus its categorized payload."""

    id: str
    label: str
    file_name: str
    receipt: dict[str, Any]


def load_examples(seed_dir: Path, data_dir: Path) -> list[ExampleReceipt]:
    """Load manifest from seed_dir; prefer receipt bodies from the shared data volume."""
    manifest_path = seed_dir / "examples.json"
    if not manifest_path.is_file():
        return []

    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    examples: list[ExampleReceipt] = []
    for entry in raw:
        file_name = entry["file"]
        receipt_path = data_dir / file_name
        if not receipt_path.is_file():
            receipt_path = seed_dir / file_name
        if not receipt_path.is_file():
            continue
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        examples.append(
            ExampleReceipt(
                id=entry["id"],
                label=entry["label"],
                file_name=file_name,
                receipt=receipt,
            )
        )
    return examples


def get_example(examples: list[ExampleReceipt], example_id: str | None) -> ExampleReceipt | None:
    """Return the selected example, or the first one when id is missing/unknown."""
    if not examples:
        return None
    if example_id:
        for example in examples:
            if example.id == example_id:
                return example
    return examples[0]
