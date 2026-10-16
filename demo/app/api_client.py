"""HTTP client for the sibling Receipt Intelligence API."""

from __future__ import annotations

from typing import Any

import httpx


class ApiError(Exception):
    """Raised when the API is unreachable or returns an error response."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ReceiptApiClient:
    """Small wrapper around analytics + Q&A endpoints."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> dict[str, Any]:
        return self._get("/health")

    def summary(self, start_date: str, end_date: str) -> dict[str, Any]:
        return self._get(
            "/analytics/summary",
            params={"start_date": start_date, "end_date": end_date},
        )

    def ask(
        self,
        question: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """POST a question; include the visible window when the API accepts it.

        ``POST /questions`` historically takes only ``question``. Extra date
        fields are ignored by most Pydantic models and rejected (422) by
        ``extra='forbid'``. On 422 we retry with the question alone so the
        demo still answers; the window also goes in the question text.
        """
        body: dict[str, Any] = {"question": question}
        if start_date and end_date:
            body["start_date"] = start_date
            body["end_date"] = end_date
            try:
                return self._post("/questions", json_body=body)
            except ApiError as exc:
                if exc.status_code == 422:
                    return self._post("/questions", json_body={"question": question})
                raise
        return self._post("/questions", json_body=body)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = httpx.get(
                f"{self.base_url}{path}",
                params=params,
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise ApiError(f"API unreachable at {self.base_url}: {exc}") from exc
        return self._parse(response)

    def _post(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self.base_url}{path}",
                json=json_body,
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise ApiError(f"API unreachable at {self.base_url}: {exc}") from exc
        return self._parse(response)

    @staticmethod
    def _parse(response: httpx.Response) -> dict[str, Any]:
        if response.status_code >= 400:
            detail = response.text.strip() or response.reason_phrase
            try:
                payload = response.json()
                if isinstance(payload, dict) and payload.get("detail"):
                    detail = str(payload["detail"])
            except ValueError:
                pass
            raise ApiError(detail, status_code=response.status_code)
        data = response.json()
        if not isinstance(data, dict):
            raise ApiError("Unexpected API response shape")
        return data
