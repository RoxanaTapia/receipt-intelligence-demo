"""Q&A window rewriting so undated questions hit the demo corpus."""

from __future__ import annotations

from app.questions import (
    SUGGESTED_QUESTIONS,
    apply_demo_window,
    enrich_question_months,
    prepare_question,
    question_has_time_window,
)


def test_bare_month_gets_demo_year() -> None:
    out = enrich_question_months(
        "How much did I spend on drinks in July?",
        year=2026,
    )
    assert out == "How much did I spend on drinks in July 2026?"


def test_question_with_year_is_left_alone() -> None:
    src = "How much did I spend on drinks in July 2026?"
    assert enrich_question_months(src, year=2024) == src


def test_undated_question_gets_visible_window() -> None:
    out = apply_demo_window(
        "How much did I spend per category?",
        "2026-07-01",
        "2026-08-31",
    )
    assert out == (
        "How much did I spend per category from 2026-07-01 to 2026-08-31?"
    )


def test_dated_question_does_not_get_a_second_window() -> None:
    src = "How much did I spend on food in August 2026?"
    assert question_has_time_window(src)
    assert apply_demo_window(src, "2026-07-01", "2026-08-31") == src


def test_prepare_question_pins_undated_prompt_to_filter_span() -> None:
    out = prepare_question(
        "How much did I spend per category?",
        window_start="2026-07-01",
        window_end="2026-08-31",
    )
    assert "2026-07-01" in out
    assert "2026-08-31" in out
    assert out.startswith("How much did I spend per category")


def test_prepare_question_adds_year_without_appending_iso_range() -> None:
    out = prepare_question(
        "How much did I spend on drinks in July?",
        window_start="2026-07-01",
        window_end="2026-08-31",
    )
    assert out == "How much did I spend on drinks in July 2026?"
    assert "2026-07-01" not in out


def test_suggested_questions_are_category_plus_month() -> None:
    assert SUGGESTED_QUESTIONS
    for prompt in SUGGESTED_QUESTIONS:
        assert "spend" in prompt.lower()
        assert any(
            month in prompt
            for month in ("July", "August")
        )
