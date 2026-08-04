"""Allowlisted demo sample PDF — download + upload validation."""

from __future__ import annotations

import hashlib
from pathlib import Path

# Primary visitor sample (must match n8n allowlist id → <id>.pdf on the samples mount).
SAMPLE_ID = "03-small"
SAMPLE_FILENAME = f"{SAMPLE_ID}.pdf"
# Vendored copy under demo/samples/ — keep in sync with n8n samples/receipts/03-small.pdf.
SAMPLE_SHA256 = "42eebc8839e83b0b076642cd4dac0e79457da57d41cfba97f27ff076e57eb2f7"


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
