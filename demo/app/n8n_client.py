"""Internal client for the n8n demo-sample ingest webhook."""

from __future__ import annotations

from typing import Any

import httpx


class N8nIngestError(Exception):
    """Raised when the n8n webhook is unreachable or returns a failure payload."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class N8nIngestClient:
    """POST sample id to n8n; response arrives after persist (or error)."""

    def __init__(self, webhook_url: str, timeout: float = 180.0) -> None:
        self.webhook_url = webhook_url.rstrip("/")
        self.timeout = timeout

    def trigger_sample(self, sample_id: str) -> dict[str, Any]:
        """Trigger allowlisted ingest. n8n reads the mounted PDF — no binary upload."""
        try:
            response = httpx.post(
                self.webhook_url,
                json={"sample": sample_id},
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise N8nIngestError(
                f"n8n webhook unreachable at {self.webhook_url}: {exc}"
            ) from exc
        return self._parse(response)

    @staticmethod
    def _parse(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            detail = response.text.strip() or response.reason_phrase
            raise N8nIngestError(
                f"n8n returned a non-JSON response ({response.status_code}): {detail}",
                status_code=response.status_code,
            ) from exc

        if not isinstance(payload, dict):
            raise N8nIngestError(
                "Unexpected n8n response shape",
                status_code=response.status_code,
            )

        if response.status_code >= 400 or payload.get("ok") is False:
            message = (
                str(payload.get("message") or payload.get("error") or response.reason_phrase)
            )
            errors = payload.get("errors")
            if isinstance(errors, list) and errors:
                message = f"{message}: {'; '.join(str(e) for e in errors)}"
            raise N8nIngestError(message, status_code=response.status_code)

        if not payload.get("persistedFilename"):
            raise N8nIngestError(
                "n8n response missing persistedFilename",
                status_code=response.status_code,
            )
        return payload
