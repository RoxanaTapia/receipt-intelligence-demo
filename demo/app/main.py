"""Visitor demo: pick an example receipt, view spending context, ask a question."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api_client import ApiError, ReceiptApiClient
from app.examples import get_example, load_examples

APP_DIR = Path(__file__).resolve().parent
SEED_DIR = Path(os.getenv("SEED_DIR", str(APP_DIR.parent / "seed")))
RECEIPT_DATA_PATH = Path(os.getenv("RECEIPT_DATA_PATH", "/data/receipts"))
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
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


def _base_context(request: Request) -> dict:
    return {
        "request": request,
        "root_path": ROOT_PATH,
        "public_url": public_url,
        "demo_css": DEMO_CSS,
        "demo_start": DEMO_START_DATE,
        "demo_end": DEMO_END_DATE,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request, example: str | None = None) -> HTMLResponse:
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
            "answer": None,
            "question": "",
            "qa_error": None,
        },
    )


@app.post("/ask", response_class=HTMLResponse)
def ask(
    request: Request,
    question: str = Form(...),
    example: str = Form(""),
) -> HTMLResponse:
    examples = load_examples(SEED_DIR, RECEIPT_DATA_PATH)
    selected = get_example(examples, example or None)
    summary = None
    api_error = None
    api_ok = False
    answer = None
    qa_error = None
    cleaned = question.strip()

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
        },
    )


@app.get("/ask")
def ask_get() -> RedirectResponse:
    return RedirectResponse(url=public_url("/"), status_code=303)
