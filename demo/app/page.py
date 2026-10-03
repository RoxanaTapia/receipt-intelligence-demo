"""Assemble the visitor page from examples, the live panel, and spending contrast."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.examples import get_example, load_examples, load_live_imports
from app.live_panel import _resolve_live_panel
from app.money import DEMO_CURRENCY, format_money
from app.sample import SAMPLE_FILENAME, SAMPLE_ID, sample_pdf_path
from app.spending import _spending_contrast

APP_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def _base_context(request: Request) -> dict[str, Any]:
    # ROOT_PATH and public_url stay in main.py (the /app prefix).
    from app.main import (
        DEMO_CSS,
        DEMO_END_DATE,
        DEMO_START_DATE,
        ROOT_PATH,
        public_url,
    )

    return {
        "request": request,
        "root_path": ROOT_PATH,
        "public_url": public_url,
        "demo_css": DEMO_CSS,
        "demo_start": DEMO_START_DATE,
        "demo_end": DEMO_END_DATE,
        "demo_currency": DEMO_CURRENCY,
        "money": format_money,
        "sample_id": SAMPLE_ID,
        "sample_filename": SAMPLE_FILENAME,
    }


def _page(
    request: Request,
    *,
    example: str | None = None,
    question: str = "",
    answer: dict[str, Any] | None = None,
    qa_error: str | None = None,
    live_receipt: dict[str, Any] | None = None,
    live_meta: dict[str, Any] | None = None,
    live_error: str | None = None,
    ingest_ok: bool = False,
    summary_before: dict[str, Any] | None = None,
    window_start: str | None = None,
    window_end: str | None = None,
) -> HTMLResponse:
    from app.main import (
        RECEIPT_DATA_PATH,
        SAMPLES_DIR,
        SEED_DIR,
        _parse_window,
        _safe_summary,
    )

    start, end = _parse_window(window_start, window_end)
    examples = load_examples(SEED_DIR, RECEIPT_DATA_PATH)
    live_imports = load_live_imports(SEED_DIR, RECEIPT_DATA_PATH)
    selected = get_example(examples, example, live_imports=live_imports)
    summary, api_error = _safe_summary(start, end)
    api_ok = summary is not None and api_error is None
    panel_receipt, panel_example = _resolve_live_panel(
        live_receipt, selected, live_imports
    )
    contrast = _spending_contrast(
        summary=summary,
        summary_before=summary_before,
        start=start,
        end=end,
        panel_receipt=panel_receipt,
        seed_dir=SEED_DIR,
    )

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            **_base_context(request),
            "examples": examples,
            "live_imports": live_imports,
            "selected": selected,
            "summary": summary,
            "summary_before": summary_before,
            **contrast,
            "window_start": start,
            "window_end": end,
            "api_ok": api_ok,
            "api_error": api_error,
            "answer": answer,
            "question": question,
            "qa_error": qa_error,
            "live_receipt": live_receipt,
            "live_panel": panel_receipt,
            "live_panel_example": panel_example,
            "live_meta": live_meta,
            "live_error": live_error,
            "ingest_ok": ingest_ok,
            "sample_ready": sample_pdf_path(SAMPLES_DIR).is_file(),
        },
    )
