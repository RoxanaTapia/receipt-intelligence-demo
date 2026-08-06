"""Visitor demo: seed examples, live sample PDF ingest, spending context, Q&A."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api_client import ApiError, ReceiptApiClient
from app.examples import get_example, load_examples, load_live_imports
from app.money import DEMO_CURRENCY, enrich_question_months, format_money, present_answer_text
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
# Explicit seed + live-sample window — analytics is corpus-wide; dates keep the demo stable.
DEMO_START_DATE = os.getenv("DEMO_START_DATE", "2026-07-01")
DEMO_END_DATE = os.getenv("DEMO_END_DATE", "2026-08-31")
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
        "demo_currency": DEMO_CURRENCY,
        "money": format_money,
        "sample_id": SAMPLE_ID,
        "sample_filename": SAMPLE_FILENAME,
    }


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


def _category_share_map(summary: dict[str, Any] | None) -> dict[str, dict[str, float]]:
    """Map category → {spend, pct} from a summary payload."""
    if not summary:
        return {}
    rows = summary.get("by_category") or []
    out: dict[str, dict[str, float]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("category") or "")
        if not name:
            continue
        out[name] = {
            "spend": float(row.get("total_spend") or 0),
            "pct": float(row.get("percentage") or 0),
        }
    return out


def _seed_baseline_spend(start: str, end: str) -> float:
    """Sum line prices on seed fixtures inside the selected window (for UX contrast)."""
    total = 0.0
    for path in sorted(SEED_DIR.glob("2026-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        receipt_date = str(data.get("date") or "")
        if receipt_date < start or receipt_date > end:
            continue
        for item in data.get("line_items") or []:
            if isinstance(item, dict):
                total += float(item.get("price") or 0)
    return round(total, 2)


def _outside_window(receipt: dict[str, Any] | None, start: str, end: str) -> bool:
    """True when a live receipt date falls outside the spending filter."""
    if not receipt:
        return False
    receipt_date = str(receipt.get("date") or "")
    if not receipt_date:
        return False
    return receipt_date < start or receipt_date > end


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
    start, end = _parse_window(window_start, window_end)
    examples = load_examples(SEED_DIR, RECEIPT_DATA_PATH)
    # Resolve live ids after ingest / deep links without listing them in the sidebar.
    live_imports = load_live_imports(SEED_DIR, RECEIPT_DATA_PATH)
    selected = get_example(examples, example, live_imports=live_imports)
    summary, api_error = _safe_summary(start, end)
    api_ok = summary is not None and api_error is None
    before_map = _category_share_map(summary_before)
    spend_before = (
        float(summary_before["total_spend"])
        if summary_before and summary_before.get("total_spend") is not None
        else None
    )
    spend_after = (
        float(summary["total_spend"])
        if summary and summary.get("total_spend") is not None
        else None
    )
    spend_delta = None
    if spend_before is not None and spend_after is not None:
        spend_delta = round(spend_after - spend_before, 2)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            **_base_context(request),
            "examples": examples,
            "selected": selected,
            "summary": summary,
            "summary_before": summary_before,
            "spend_before": spend_before,
            "spend_after": spend_after,
            "spend_delta": spend_delta,
            "before_map": before_map,
            "seed_baseline": _seed_baseline_spend(start, end),
            "window_start": start,
            "window_end": end,
            "live_outside_window": _outside_window(live_receipt, start, end),
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
            summary_before=summary_before,
            window_start=window_start,
            window_end=window_end,
        )

    # Keep the seeded example table as-is; live result lives in the top panel only.
    return _page(
        request,
        example=example or None,
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
            text = present_answer_text(str(raw.get("answer") or ""))
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


@app.get("/ask")
def ask_get() -> RedirectResponse:
    return RedirectResponse(url=public_url("/"), status_code=303)


@app.get("/ingest")
def ingest_get() -> RedirectResponse:
    return RedirectResponse(url=public_url("/"), status_code=303)
