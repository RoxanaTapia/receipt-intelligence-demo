"""Load visitor-facing example receipts from seed JSON and live imports on disk."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


@dataclass(frozen=True)
class ExampleReceipt:
    """One pickable demo receipt plus its categorized payload."""

    id: str
    label: str
    file_name: str
    receipt: dict[str, Any]
    source: Literal["seed", "live"] = "seed"


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
                source="seed",
            )
        )
    return examples


def load_live_imports(seed_dir: Path, data_dir: Path) -> list[ExampleReceipt]:
    """Receipts on the shared volume that are not in the seed manifest (live ingest)."""
    seed_names = _manifest_file_names(seed_dir)
    imports: list[ExampleReceipt] = []
    if not data_dir.is_dir():
        return imports

    for path in sorted(data_dir.glob("*.json")):
        if path.name in seed_names:
            continue
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(receipt, dict):
            continue
        merchant = str(receipt.get("merchant") or "Live receipt").strip() or "Live receipt"
        date = str(receipt.get("date") or "").strip()
        label = f"{merchant} — {date}" if date else merchant
        imports.append(
            ExampleReceipt(
                id=f"live-{path.stem}",
                label=label,
                file_name=path.name,
                receipt=receipt,
                source="live",
            )
        )
    return imports


def get_example(
    examples: list[ExampleReceipt],
    example_id: str | None,
    *,
    live_imports: list[ExampleReceipt] | None = None,
) -> ExampleReceipt | None:
    """Return the selected seed or live receipt; default to the first seed."""
    live_imports = live_imports or []
    catalog = [*examples, *live_imports]
    if not catalog:
        return None
    if example_id:
        for example in catalog:
            if example.id == example_id:
                return example
    return examples[0] if examples else live_imports[0]


def delete_live_import(seed_dir: Path, data_dir: Path, example_id: str) -> bool:
    """Remove a live-ingest JSON from the shared volume; never delete seed fixtures."""
    if not example_id.startswith("live-"):
        return False
    stem = example_id.removeprefix("live-")
    if not stem or "/" in stem or "\\" in stem or stem in {".", ".."}:
        return False
    path = data_dir / f"{stem}.json"
    if not path.is_file():
        return False
    if path.name in _manifest_file_names(seed_dir):
        return False
    try:
        path.unlink()
    except OSError:
        return False
    return True


def _manifest_file_names(seed_dir: Path) -> set[str]:
    manifest_path = seed_dir / "examples.json"
    if not manifest_path.is_file():
        return set()
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    names: set[str] = set()
    for entry in raw:
        if isinstance(entry, dict) and entry.get("file"):
            names.add(str(entry["file"]))
    return names
