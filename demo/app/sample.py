"""Allowlisted demo sample PDF — download + upload validation."""

from __future__ import annotations

import hashlib
from pathlib import Path

# Must match n8n's sample id → ``{id}.pdf`` on the samples mount.
SAMPLE_ID = "sample-supermarket-receipt"
SAMPLE_FILENAME = f"{SAMPLE_ID}.pdf"
# Vendored copy under demo/samples/ — regenerate with scripts/generate_sample_receipt.py.
SAMPLE_SHA256 = "9d494c29a96fea3f56c03d1161bbccb76901463647ed3ae2bc9970c17aa3a014"


def sample_pdf_path(samples_dir: Path) -> Path:
    """Path to the vendored demo sample PDF."""
    return samples_dir / SAMPLE_FILENAME


def validate_demo_sample(filename: str | None, content: bytes) -> str | None:
    """Return an error message if upload is not the known demo sample; else None."""
    if not content:
        return "Upload is empty. Download the demo sample PDF and upload that file."
    digest = hashlib.sha256(content).hexdigest()
    if digest != SAMPLE_SHA256:
        return (
            "This file is not the demo sample. "
            "Download the sample PDF from this page and upload that file."
        )
    # Filename is a soft check — hash is authoritative.
    if filename and Path(filename).name.lower() not in {
        SAMPLE_FILENAME.lower(),
        SAMPLE_ID.lower(),
    }:
        # Still accept if hash matches (browser may rename on save).
        pass
    return None
