"""Visitor demo: seed examples, live sample PDF ingest, spending context, Q&A."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api_client import ApiError, ReceiptApiClient
from app.examples import get_example, load_examples
from app.n8n_client import N8nIngestClient, N8nIngestError
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
# Explicit seed window — analytics is corpus-wide; dates keep the demo stable.
DEMO_START_DATE = os.getenv("DEMO_START_DATE", "2026-05-01")
DEMO_END_DATE = os.getenv("DEMO_END_DATE", "2026-05-31")
# Public URL prefix as seen by the browser (e.g. "/app" behind Caddy handle_path).
# Keep empty for local host publish on :8080. Shared-edge / solo Caddy set /app.
ROOT_PATH = os.getenv("ROOT_PATH", "").rstrip("/")
# Inlined so the demo stays styled even if /app/static/* is mis-proxied.
DEMO_CSS = (APP_DIR / "static" / "demo.css").read_text(encoding="utf-8")


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
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
api = ReceiptApiClient(API_BASE_URL)
n8n = N8nIngestClient(N8N_INGEST_WEBHOOK_URL)


def _base_context(request: Request) -> dict[str, Any]:
    return {
        "request": request,
        "root_path": ROOT_PATH,
        "public_url": public_url,
        "demo_css": DEMO_CSS,
        "demo_start": DEMO_START_DATE,
        "demo_end": DEMO_END_DATE,
        "sample_id": SAMPLE_ID,
        "sample_filename": SAMPLE_FILENAME,
    }


def _load_persisted_receipt(filename: str) -> dict[str, Any] | None:
    """Read categorized JSON from the shared receipts volume."""
    path = RECEIPT_DATA_PATH / Path(filename).name
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


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
) -> HTMLResponse:
    examples = load_examples(SEED_DIR, RECEIPT_DATA_PATH)
    selected = get_example(examples, example)
    summary = None
    api_error = None
    api_ok = False

    try:
        api.health()
        api_ok = True
        summary = api.summary(DEMO_START_DATE, DEMO_END_DATE)
    except ApiError as exc:
        api_error = str(exc)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            **_base_context(request),
            "examples": examples,
            "selected": selected,
            "summary": summary,
            "api_ok": api_ok,
            "api_error": api_error,
            "answer": answer,
            "question": question,
            "qa_error": qa_error,
            "live_receipt": live_receipt,
            "live_meta": live_meta,
            "live_error": live_error,
            "ingest_ok": ingest_ok,
            "sample_ready": sample_pdf_path(SAMPLES_DIR).is_file(),
        },
    )


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
def index(request: Request, example: str | None = None) -> HTMLResponse:
    return _page(request, example=example)


@app.post("/ingest", response_class=HTMLResponse)
async def ingest(
    request: Request,
    pdf: UploadFile = File(...),
    example: str = Form(""),
) -> HTMLResponse:
    """Validate uploaded sample, trigger n8n webhook, show persisted categories."""
    content = await pdf.read()
    reject = validate_demo_sample(pdf.filename, content)
    if reject:
        return _page(request, example=example or None, live_error=reject)

    try:
        meta = n8n.trigger_sample(SAMPLE_ID)
    except N8nIngestError as exc:
        return _page(
            request,
            example=example or None,
            live_error=(
                f"{exc} — Import alone is not enough: the ingest workflow must be "
                "Active/Published in /n8n* (see DEPLOYMENT.md § Live sample PDF)."
            ),
        )

    filename = str(meta["persistedFilename"])
    receipt = _load_persisted_receipt(filename)
    if receipt is None:
        return _page(
            request,
            example=example or None,
            live_meta=meta,
            live_error=(
                f"Ingest reported {filename}, but the file is not visible on the "
                "shared receipts volume yet. Refresh in a moment or check n8n."
            ),
            ingest_ok=True,
        )

    return _page(
        request,
        example=example or None,
        live_receipt=receipt,
        live_meta=meta,
        ingest_ok=True,
    )


@app.post("/ask", response_class=HTMLResponse)
def ask(
    request: Request,
    question: str = Form(...),
    example: str = Form(""),
) -> HTMLResponse:
    cleaned = question.strip()
    examples = load_examples(SEED_DIR, RECEIPT_DATA_PATH)
    selected = get_example(examples, example or None)
    summary = None
    api_error = None
    api_ok = False
    answer = None
    qa_error = None

    try:
        api.health()
        api_ok = True
        summary = api.summary(DEMO_START_DATE, DEMO_END_DATE)
        if not cleaned:
            qa_error = "Enter a budget question first."
        else:
            answer = api.ask(cleaned)
    except ApiError as exc:
        if api_ok:
            qa_error = str(exc)
        else:
            api_error = str(exc)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            **_base_context(request),
            "examples": examples,
            "selected": selected,
            "summary": summary,
            "api_ok": api_ok,
            "api_error": api_error,
            "answer": answer,
            "question": cleaned,
            "qa_error": qa_error,
            "live_receipt": None,
            "live_meta": None,
            "live_error": None,
            "ingest_ok": False,
            "sample_ready": sample_pdf_path(SAMPLES_DIR).is_file(),
        },
    )


@app.get("/ask")
def ask_get() -> RedirectResponse:
    return RedirectResponse(url=public_url("/"), status_code=303)


@app.get("/ingest")
def ingest_get() -> RedirectResponse:
    return RedirectResponse(url=public_url("/"), status_code=303)
