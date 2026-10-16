"""Allowlisted sample validation and generator hash lock."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

from app.sample import SAMPLE_FILENAME, SAMPLE_SHA256, validate_demo_sample
from app.sample_receipt import ITEMS, MERCHANT, receipt_total


def test_empty_upload_is_rejected() -> None:
    assert validate_demo_sample(SAMPLE_FILENAME, b"") is not None


def test_wrong_bytes_are_rejected() -> None:
    message = validate_demo_sample(SAMPLE_FILENAME, b"%PDF-not-the-sample")
    assert message is not None
    assert "not the demo sample" in message


def test_vendored_pdf_matches_allowlist_hash() -> None:
    path = Path(__file__).resolve().parents[1] / "samples" / SAMPLE_FILENAME
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == SAMPLE_SHA256
    assert validate_demo_sample(SAMPLE_FILENAME, path.read_bytes()) is None


def test_sample_is_a_readable_supermarket_receipt() -> None:
    assert SAMPLE_FILENAME == "sample-supermarket-receipt.pdf"
    assert MERCHANT == "Green Basket Market"
    assert 8 <= len(ITEMS) <= 12
    assert receipt_total() == 25.0
    depts = {str(item["dept"]) for item in ITEMS}
    assert depts == {"Produce", "Dairy", "Drinks", "Bakery", "Household"}


def test_generator_output_matches_allowlist_hash() -> None:
    path = Path(__file__).resolve().parents[1] / "scripts" / "generate_sample_receipt.py"
    spec = importlib.util.spec_from_file_location("generate_sample_receipt", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    digest = hashlib.sha256(mod.build_pdf()).hexdigest()
    assert digest == SAMPLE_SHA256
