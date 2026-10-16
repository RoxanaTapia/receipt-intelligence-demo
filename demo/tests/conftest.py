"""Shared fixtures for the visitor demo app."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.sample import SAMPLE_ID
from app.sample_receipt import MERCHANT, receipt_payload

SEED_DIR = Path(__file__).resolve().parents[1] / "seed"


class FakeApi:
    """Stand-in for the companion analytics/Q&A API."""

    def __init__(self) -> None:
        self.questions: list[dict[str, str | None]] = []
        self.summary_payload = {
            "total_spend": 54.5,
            "by_category": [
                {"category": "drinks", "total_spend": 9.2, "percentage": 16.9},
                {"category": "food", "total_spend": 21.2, "percentage": 38.9},
                {"category": "household", "total_spend": 16.1, "percentage": 29.5},
                {"category": "snacks", "total_spend": 8.0, "percentage": 14.7},
            ],
        }

    def health(self) -> dict[str, str]:
        return {"status": "ok"}

    def summary(self, start_date: str, end_date: str) -> dict:
        return dict(self.summary_payload)

    def ask(
        self,
        question: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, str]:
        self.questions.append(
            {
                "question": question,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
        q = question.lower()
        if "drink" in q and "august" in q:
            return {"answer": "You spent 4.10 DC on drinks in August."}
        if "per category" in q or "by category" in q:
            return {
                "answer": (
                    "Drinks 9.20 DC (including 5.10 DC in July), "
                    "food 21.20 DC, household 16.10 DC, snacks 8.00 DC."
                )
            }
        return {"answer": "You spent $5.10 on drinks in July."}


class FakeN8n:
    """Stand-in that writes the Green Basket Market JSON like n8n persist."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.calls: list[str] = []
        self.filename = "2026-08-15_green-basket-market_abcd1234.json"
        self.receipt = receipt_payload()

    def trigger_sample(self, sample_id: str) -> dict:
        self.calls.append(sample_id)
        path = self.data_dir / self.filename
        path.write_text(json.dumps(self.receipt), encoding="utf-8")
        return {
            "ok": True,
            "persistedFilename": self.filename,
            "merchant": self.receipt["merchant"],
        }


@pytest.fixture
def fake_api(monkeypatch: pytest.MonkeyPatch) -> FakeApi:
    api = FakeApi()
    monkeypatch.setattr(main, "api", api)
    return api


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(main, "RECEIPT_DATA_PATH", tmp_path)
    monkeypatch.setattr(main, "SEED_DIR", SEED_DIR)
    return tmp_path


@pytest.fixture
def fake_n8n(data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> FakeN8n:
    n8n = FakeN8n(data_dir)
    monkeypatch.setattr(main, "n8n", n8n)
    return n8n


@pytest.fixture
def client(fake_api: FakeApi, data_dir: Path, fake_n8n: FakeN8n) -> TestClient:
    return TestClient(main.app)


@pytest.fixture
def sample_id() -> str:
    return SAMPLE_ID
