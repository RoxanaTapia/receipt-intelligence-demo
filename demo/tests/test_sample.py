"""Allowlisted sample validation."""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.sample import SAMPLE_FILENAME, SAMPLE_SHA256, validate_demo_sample


def test_empty_upload_is_rejected() -> None:
    assert validate_demo_sample("05-demo-basket.pdf", b"") is not None


def test_wrong_bytes_are_rejected() -> None:
    message = validate_demo_sample("05-demo-basket.pdf", b"%PDF-not-the-sample")
    assert message is not None
    assert "not the demo sample" in message


def test_vendored_pdf_matches_allowlist_hash() -> None:
    path = Path(__file__).resolve().parents[1] / "samples" / SAMPLE_FILENAME
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == SAMPLE_SHA256
    assert validate_demo_sample(SAMPLE_FILENAME, path.read_bytes()) is None
