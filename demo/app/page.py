"""Assemble the visitor page from examples, the live panel, and spending contrast."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.examples import ExampleReceipt, get_example, session_catalog
from app.live_panel import (
    _resolve_live_panel,
    format_answer_time,
    format_read_summary,
    line_item_count,
)
from app.money import DEMO_CURRENCY, format_money
from app.questions import SUGGESTED_QUESTIONS
from app.receipt_answers import CaseView, merchant_name, receipt_list_rows, story_date
from app.sample import SAMPLE_FILENAME, SAMPLE_ID, SAMPLE_VISITOR_NAME, sample_pdf_path
from app.sample_receipt import DATE as SAMPLE_DATE
from app.sample_receipt import MERCHANT as SAMPLE_MERCHANT
from app.session import (
    apply_session_cookies,
    owned_filenames,
    remember_import,
    session_id,
)
from app.spending import _spending_contrast

APP_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


def parse_posted_step(raw: str | int | None) -> int | None:
    """Return 1, 2, or 3 when an extract form posted the stepper's current step."""
    if raw is None:
        return None
    text = str(raw).strip()
    if text not in {"1", "2", "3"}:
        return None
    return int(text)


def _base_context(request: Request) -> dict[str, Any]:
    # ROOT_PATH and public_url stay in main.py (the /app prefix).
    from app.main import (
        DEMO_CSS,
        DEMO_END_DATE,
        DEMO_START_DATE,
        ROOT_PATH,
        operator_session,
        public_url,
    )

    return {
        "request": request,
        "root_path": ROOT_PATH,
        "public_url": public_url,
        "operator": operator_session(request),
        "demo_css": DEMO_CSS,
        "demo_start": DEMO_START_DATE,
        "demo_end": DEMO_END_DATE,
        "demo_currency": DEMO_CURRENCY,
        "money": format_money,
        "story_date": story_date,
        "sample_id": SAMPLE_ID,
        "sample_filename": SAMPLE_FILENAME,
        "sample_visitor_name": SAMPLE_VISITOR_NAME,
        "suggested_questions": SUGGESTED_QUESTIONS,
    }


def _page(
    request: Request,
    *,
    example: str | None = None,
    question: str = "",
    answer: dict[str, Any] | None = None,
    answer_source: str | None = None,
    qa_error: str | None = None,
    live_receipt: dict[str, Any] | None = None,
    live_meta: dict[str, Any] | None = None,
    live_error: str | None = None,
    ingest_ok: bool = False,
    ingest_elapsed: float | None = None,
    ask_elapsed: float | None = None,
    case_answer: CaseView | None = None,
    summary_before: dict[str, Any] | None = None,
    window_start: str | None = None,
    window_end: str | None = None,
    preserve_step: int | None = None,
) -> HTMLResponse:
    from app.main import (
        RECEIPT_DATA_PATH,
        SAMPLES_DIR,
        SEED_DIR,
        _parse_window,
        _safe_summary,
    )

    start, end = _parse_window(window_start, window_end)
    sid = session_id(request)
    owned = owned_filenames(request)
    if live_meta:
        owned = remember_import(owned, str(live_meta.get("persistedFilename") or ""))

    examples, live_imports = session_catalog(SEED_DIR, RECEIPT_DATA_PATH, owned)
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
    if answer or qa_error:
        scroll_target = "ask-answer"
        flow_step = 3
    elif ingest_ok or panel_receipt:
        scroll_target = "live-ingest" if ingest_ok else ""
        flow_step = 2
    else:
        scroll_target = ""
        flow_step = 1
    # A second extract re-renders the page. Keep a later step the visitor
    # already reached, and keep whatever they typed in the question box.
    kept = parse_posted_step(preserve_step)
    if kept is not None and kept > flow_step:
        flow_step = kept
        if kept >= 3:
            scroll_target = ""

    source = answer_source or ""
    elapsed = ingest_elapsed
    if elapsed is None:
        raw = request.cookies.get("demo_read_s")
        try:
            elapsed = float(raw) if raw is not None else None
        except ValueError:
            elapsed = None
    read_summary = ""
    if panel_receipt:
        read_summary = format_read_summary(line_item_count(panel_receipt), elapsed)

    response = templates.TemplateResponse(
        request,
        "index.html",
        {
            **_base_context(request),
            "examples": examples,
            "live_imports": live_imports,
            "august_cards": _august_cards(examples, live_imports),
            "your_receipts": receipt_list_rows(examples, live_imports),
            "selected": selected,
            "picked_example": bool(example),
            "summary": summary,
            "summary_before": summary_before,
            **contrast,
            "window_start": start,
            "window_end": end,
            "api_ok": api_ok,
            "api_error": api_error,
            "answer": answer,
            "answer_source": source if answer and answer.get("answer") else "",
            "answer_time": format_answer_time(ask_elapsed) if answer else "",
            "ask_elapsed": ask_elapsed,
            "case_answer": case_answer if answer else None,
            "cited_lines": list(case_answer.cited) if case_answer and answer else [],
            "question": question,
            "qa_error": qa_error,
            "live_receipt": live_receipt,
            "live_panel": panel_receipt,
            "live_panel_example": panel_example,
            "live_meta": live_meta,
            "live_error": live_error,
            "ingest_ok": ingest_ok,
            "read_summary": read_summary,
            "read_count": line_item_count(panel_receipt) if panel_receipt else 0,
            "read_seconds": elapsed,
            "sample_ready": sample_pdf_path(SAMPLES_DIR).is_file(),
            "scroll_target": scroll_target,
            "flow_step": flow_step,
        },
    )
    apply_session_cookies(response, sid, owned)
    if ingest_elapsed is not None:
        response.set_cookie(
            "demo_read_s",
            f"{ingest_elapsed:.3f}",
            max_age=60 * 60 * 12,
            httponly=True,
            samesite="lax",
            path="/",
        )
    return response


def _august_cards(
    examples: list[ExampleReceipt],
    live_imports: list[ExampleReceipt],
) -> list[dict[str, Any]]:
    """Three seeded receipts, then Green Basket Market marked new.

    The new card is a label until this session reads the allowlisted sample.
    """
    seeded = [_seed_card(item) for item in examples]
    fresh = next(
        (
            item
            for item in live_imports
            if merchant_name(item.receipt) == SAMPLE_MERCHANT
        ),
        None,
    )
    if fresh is not None:
        new_card = _seed_card(fresh, is_new=True, read=True)
    else:
        new_card = {
            "merchant": SAMPLE_MERCHANT,
            "when": story_date(SAMPLE_DATE),
            "total_label": "",
            "is_new": True,
            "read": False,
        }
    others = [
        _seed_card(item, is_new=True, read=True)
        for item in live_imports
        if merchant_name(item.receipt) != SAMPLE_MERCHANT
    ]
    # The receipt you can read sits first, so a phone reaches it without a hunt.
    return [new_card, *seeded, *others]


def _seed_card(
    item: ExampleReceipt, *, is_new: bool = False, read: bool = False
) -> dict[str, Any]:
    receipt = item.receipt
    total = receipt.get("total")
    try:
        total_label = format_money(float(total)) if total is not None else ""
    except (TypeError, ValueError):
        total_label = ""
    raw_date = str(receipt.get("date") or "")
    return {
        "merchant": merchant_name(receipt),
        "when": story_date(raw_date) if raw_date else "",
        "total_label": total_label,
        "is_new": is_new,
        "read": read,
    }
