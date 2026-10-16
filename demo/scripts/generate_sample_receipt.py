#!/usr/bin/env python3
"""Generate the allowlisted supermarket sample PDF (reportlab).

Run from repo root or demo/:

    python3 demo/scripts/generate_sample_receipt.py

Writes ``demo/samples/sample-supermarket-receipt.pdf`` with frozen metadata
so the SHA-256 stays stable. Then copy the printed hash into
``demo/app/sample.py`` (``SAMPLE_SHA256``).
"""

from __future__ import annotations

import hashlib
import re
import sys
from collections import defaultdict
from io import BytesIO
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.sample_receipt import (  # noqa: E402
    ADDRESS_LINES,
    CURRENCY,
    DATE,
    ITEMS,
    MERCHANT,
    receipt_total,
)

OUT_PATH = ROOT / "samples" / "sample-supermarket-receipt.pdf"
PAGE_W = 110 * mm
# Tall receipt roll — 10 lines plus department headers still breathe.
PAGE_H = 210 * mm
MARGIN_X = 10 * mm
FROZEN_DATE = "D:20260815000000+00'00'"
# 32 hex chars — same width as ReportLab's default /ID so xref offsets stay put.
FROZEN_ID_HEX = "a1b2c3d4e5f60718293a4b5c6d7e8f90"


def _draw_rule(c: canvas.Canvas, y: float, pattern: str = "· ") -> float:
    c.setFont("Courier", 10)
    c.setFillColorRGB(0.15, 0.16, 0.18)
    c.drawCentredString(PAGE_W / 2, y, (pattern * 28)[:28])
    return y - 14


def _money(value: float) -> str:
    return f"{value:.2f} {CURRENCY}"


def build_pdf() -> bytes:
    """Render a large-type supermarket receipt into deterministic PDF bytes."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    c.setTitle(f"{MERCHANT} — sample receipt")
    c.setAuthor("Receipt Intelligence demo")
    c.setSubject("Allowlisted demo supermarket receipt (DC)")
    c.setCreator("demo/scripts/generate_sample_receipt.py")
    c.setProducer("receipt-intelligence-demo")
    c.setFillColorRGB(0.12, 0.13, 0.15)

    y = PAGE_H - 16 * mm
    c.setFont("Times-Bold", 22)
    c.drawCentredString(PAGE_W / 2, y, MERCHANT)
    y -= 18
    c.setFont("Times-Roman", 12)
    for line in ADDRESS_LINES:
        c.drawCentredString(PAGE_W / 2, y, line)
        y -= 15
    y -= 4
    y = _draw_rule(c, y)
    c.setFont("Times-Bold", 14)
    c.drawCentredString(PAGE_W / 2, y, "SAMPLE RECEIPT")
    y -= 18
    c.setFont("Times-Roman", 13)
    # Date inside the Jul–Aug 2026 demo window, written out for OCR/extract.
    c.drawCentredString(PAGE_W / 2, y, "15 August 2026")
    y -= 16
    c.setFont("Times-Roman", 11)
    c.drawCentredString(PAGE_W / 2, y, f"Date: {DATE}")
    y -= 8
    y = _draw_rule(c, y)

    grouped: dict[str, list] = defaultdict(list)
    order: list[str] = []
    for item in ITEMS:
        dept = str(item["dept"])
        if dept not in grouped:
            order.append(dept)
        grouped[dept].append(item)

    for dept in order:
        c.setFont("Times-Bold", 12)
        c.drawString(MARGIN_X, y, dept.upper())
        y -= 16
        for item in grouped[dept]:
            c.setFont("Times-Roman", 13)
            desc = str(item["description"])
            qty = int(item["quantity"])
            label = desc if qty == 1 else f"{desc}  ×{qty}"
            c.drawString(MARGIN_X, y, label)
            amount = _money(float(item["price"]))
            c.drawRightString(PAGE_W - MARGIN_X, y, amount)
            y -= 17
        y -= 6

    y = _draw_rule(c, y, "— ")
    c.setFont("Times-Bold", 16)
    c.drawString(MARGIN_X, y, "TOTAL")
    c.drawRightString(PAGE_W - MARGIN_X, y, _money(receipt_total()))
    y -= 20
    c.setFont("Times-Roman", 12)
    c.drawCentredString(PAGE_W / 2, y, f"{CURRENCY} = demo currency (not real money)")
    y -= 16
    c.setFont("Times-Roman", 11)
    c.drawCentredString(PAGE_W / 2, y, "Fictional store · Receipt Intelligence demo")
    y -= 8
    y = _draw_rule(c, y)
    c.setFont("Times-Roman", 11)
    c.drawCentredString(PAGE_W / 2, y, "Thank you for shopping")

    c.showPage()
    c.save()
    return _freeze_metadata(buf.getvalue())


def _freeze_metadata(data: bytes) -> bytes:
    """Pin dates and file IDs so regenerating the PDF does not churn the hash."""
    out = re.sub(
        rb"/CreationDate \(D:[^)]+\)",
        f"/CreationDate ({FROZEN_DATE})".encode("ascii"),
        data,
    )
    out = re.sub(
        rb"/ModDate \(D:[^)]+\)",
        f"/ModDate ({FROZEN_DATE})".encode("ascii"),
        out,
    )
    out = re.sub(
        rb"/ID\s*\[\s*<[0-9A-Fa-f]+>\s*<[0-9A-Fa-f]+>\s*\]",
        f"/ID [<{FROZEN_ID_HEX}><{FROZEN_ID_HEX}>]".encode("ascii"),
        out,
    )
    return out


def main() -> None:
    pdf = build_pdf()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_bytes(pdf)
    digest = hashlib.sha256(pdf).hexdigest()
    print(f"Wrote {OUT_PATH}")
    print(f"SHA-256 {digest}")
    print(f"Items {len(ITEMS)}  total {receipt_total():.2f} {CURRENCY}")


if __name__ == "__main__":
    main()
