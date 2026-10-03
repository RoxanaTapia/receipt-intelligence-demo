"""Visitor demo: seed examples, live sample PDF ingest, spending context, Q&A."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api_client import ApiError, ReceiptApiClient
from app.examples import delete_live_import, load_examples
from app.money import enrich_question_months, present_answer_text
from app.n8n_client import N8nIngestClient, N8nIngestError
from app.page import _page
from app.sample import SAMPLE_FILENAME, SAMPLE_ID, sample_pdf_path, validate_demo_sample

APP_DIR = Path(__file__).resolve().parent
SEED_DIR = Path(os.getenv("SEED_DIR", str(APP_DIR.parent / "seed")))
SAMPLES_DIR = Path(os.getenv("SAMPLES_DIR", str(APP_DIR.parent / "samples")))
RECEIPT_DATA_PATH = Path(os.getenv("RECEIPT_DATA_PATH", "/data/receipts"))
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
N8N_INGEST_WEBHOOK_URL = os.getenv(
    "N8N_INGEST_WEBHOOK_URL",
    "http://n8n:5678/webhook/receipt-demo-ingest",
)
# Explicit seed + live-sample window — analytics is corpus-wide; dates keep the demo stable.
DEMO_START_DATE = os.getenv("DEMO_START_DATE", "2026-07-01")
DEMO_END_DATE = os.getenv("DEMO_END_DATE", "2026-08-31")
# Public URL prefix as seen by the browser (e.g. "/app" behind Caddy handle_path).
# Keep empty for local host publish on :8080. Shared-edge / solo Caddy set /app.
ROOT_PATH = os.getenv("ROOT_PATH", "").rstrip("/")
# Inlined so the demo stays styled even if /app/static/* is mis-proxied.
# Segments are joined in the original rule order so nothing in the sheet shifts.
_CSS_SEGMENT = "\n/* segment */\n"
_CSS_ORDER = (
    "shared",
    "examples",
    "shared",
    "spending",
    "ask",
    "live",
    "spending",
    "ask",
    "shared",
    "live",
    "examples",
    "ask",
    "spending",
    "examples",
    "live",
    "shared",
    "live",
    "shared",
    "live",
)


def _load_demo_css() -> str:
    folder = APP_DIR / "static" / "panels"
    parts = {
        name: (folder / f"{name}.css").read_text(encoding="utf-8").split(_CSS_SEGMENT)
        for name in ("shared", "examples", "spending", "ask", "live")
    }
    cursor = {name: 0 for name in parts}
    chunks = []
    for name in _CSS_ORDER:
        chunks.append(parts[name][cursor[name]])
        cursor[name] += 1
    return "\n\n".join(chunks)


DEMO_CSS = _load_demo_css()


def public_url(path: str = "/") -> str:
    """Browser-facing URL under ROOT_PATH, or path-relative when ROOT_PATH is empty."""
    norm = path if path.startswith("/") else f"/{path}"
    if ROOT_PATH:
        return f"{ROOT_PATH}{norm}"
    # Relative to the current directory URL (works when the page is /app/).
    if norm == "/":
        return "./"
    return norm.lstrip("/")


app = FastAPI(title="Receipt Intelligence Demo", root_path=ROOT_PATH)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
api = ReceiptApiClient(API_BASE_URL)
n8n = N8nIngestClient(N8N_INGEST_WEBHOOK_URL)


def _parse_window(start: str | None, end: str | None) -> tuple[str, str]:
    """Normalize visitor date filters; fall back to the default demo window."""
    start_s = (start or DEMO_START_DATE).strip()
    end_s = (end or DEMO_END_DATE).strip()
    try:
        start_d = date.fromisoformat(start_s)
        end_d = date.fromisoformat(end_s)
    except ValueError:
        return DEMO_START_DATE, DEMO_END_DATE
    if start_d > end_d:
        start_d, end_d = end_d, start_d
    return start_d.isoformat(), end_d.isoformat()


def _load_persisted_receipt(filename: str) -> dict[str, Any] | None:
    """Read categorized JSON from the shared receipts volume."""
    path = RECEIPT_DATA_PATH / Path(filename).name
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def _safe_summary(start: str, end: str) -> tuple[dict[str, Any] | None, str | None]:
    """Fetch window summary; return (summary, error)."""
    try:
        api.health()
        return api.summary(start, end), None
    except ApiError as exc:
        return None, str(exc)


def _home_redirect(
    *,
    start: str,
    end: str,
    example: str | None = None,
) -> RedirectResponse:
    """303 back to the demo page with window (and optional example) query params."""
    params: dict[str, str] = {"start": start, "end": end}
    if example:
        params["example"] = example
    base = public_url("/")
    sep = "&" if "?" in base else "?"
    return RedirectResponse(url=f"{base}{sep}{urlencode(params)}", status_code=303)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/sample.pdf")
def download_sample() -> FileResponse:
    """Serve the vendored allowlisted sample for visitor download."""
    path = sample_pdf_path(SAMPLES_DIR)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Demo sample PDF is not packaged")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=SAMPLE_FILENAME,
    )


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    example: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> HTMLResponse:
    return _page(request, example=example, window_start=start, window_end=end)


@app.post("/ingest", response_class=HTMLResponse)
async def ingest(
    request: Request,
    pdf: UploadFile = File(...),
    example: str = Form(""),
    start: str = Form(""),
    end: str = Form(""),
) -> HTMLResponse:
    """Validate uploaded sample, trigger n8n webhook, show persisted categories."""
    window_start, window_end = _parse_window(start or None, end or None)
    content = await pdf.read()
    reject = validate_demo_sample(pdf.filename, content)
    if reject:
        return _page(
            request,
            example=example or None,
            live_error=reject,
            window_start=window_start,
            window_end=window_end,
        )

    # Snapshot spending before n8n writes so the UI can show before → after bars.
    summary_before, _ = _safe_summary(window_start, window_end)

    try:
        meta = n8n.trigger_sample(SAMPLE_ID)
    except N8nIngestError as exc:
        return _page(
            request,
            example=example or None,
            live_error=(
                f"{exc} — Import alone is not enough: the ingest workflow must be "
                "Active/Published in n8n (see DEPLOYMENT.md § Live sample PDF)."
            ),
            summary_before=summary_before,
            window_start=window_start,
            window_end=window_end,
        )

    filename = str(meta["persistedFilename"])
    live_example_id = f"live-{Path(filename).stem}"
    receipt = _load_persisted_receipt(filename)
    if receipt is None:
        return _page(
            request,
            example=live_example_id,
            live_meta=meta,
            live_error=(
                f"Ingest reported {filename}, but the file is not visible on the "
                "shared receipts volume yet. Refresh in a moment or check n8n."
            ),
            ingest_ok=True,
            summary_before=summary_before,
            window_start=window_start,
            window_end=window_end,
        )

    return _page(
        request,
        example=live_example_id,
        live_receipt=receipt,
        live_meta=meta,
        ingest_ok=True,
        summary_before=summary_before,
        window_start=window_start,
        window_end=window_end,
    )


@app.post("/ask", response_class=HTMLResponse)
def ask(
    request: Request,
    question: str = Form(...),
    example: str = Form(""),
    start: str = Form(""),
    end: str = Form(""),
) -> HTMLResponse:
    window_start, window_end = _parse_window(start or None, end or None)
    cleaned = question.strip()
    answer = None
    qa_error = None

    if not cleaned:
        qa_error = "Enter a budget question first."
    else:
        try:
            demo_year = int(window_start[:4])
            routed_question = enrich_question_months(cleaned, year=demo_year)
            raw = api.ask(routed_question)
            text = present_answer_text(
                str(raw.get("answer") or ""),
                window_start=window_start,
                window_end=window_end,
            )
            answer = {**raw, "answer": text} if text else raw
        except ApiError as exc:
            qa_error = str(exc)

    return _page(
        request,
        example=example or None,
        question=cleaned,
        answer=answer,
        qa_error=qa_error,
        window_start=window_start,
        window_end=window_end,
    )


@app.post("/live-import/delete", response_model=None)
def remove_live_import(
    request: Request,
    example: str = Form(...),
    start: str = Form(""),
    end: str = Form(""),
):
    """Delete a live-ingest file so the visitor can run the sample again."""
    window_start, window_end = _parse_window(start or None, end or None)
    target = example.strip()
    if not delete_live_import(SEED_DIR, RECEIPT_DATA_PATH, target):
        return _page(
            request,
            example=target,
            window_start=window_start,
            window_end=window_end,
            live_error="Could not remove that live import. It may already be gone.",
        )
    examples = load_examples(SEED_DIR, RECEIPT_DATA_PATH)
    fallback = examples[0].id if examples else None
    return _home_redirect(start=window_start, end=window_end, example=fallback)


@app.get("/ask")
def ask_get() -> RedirectResponse:
    return RedirectResponse(url=public_url("/"), status_code=303)


@app.get("/ingest")
def ingest_get() -> RedirectResponse:
    return RedirectResponse(url=public_url("/"), status_code=303)


@app.get("/live-import/delete")
def remove_live_import_get() -> RedirectResponse:
    return RedirectResponse(url=public_url("/"), status_code=303)
