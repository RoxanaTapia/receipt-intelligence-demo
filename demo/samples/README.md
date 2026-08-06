# Demo sample PDFs

Vendored allowlisted fixtures for the visitor **download → upload → ingest** path.

| File | n8n sample id | Role |
|------|---------------|------|
| [05-demo-basket.pdf](05-demo-basket.pdf) | `05-demo-basket` | **Primary** portfolio sample (fictional café; distinct from seed totals) |
| [03-small.pdf](03-small.pdf) | `03-small` | Optional smoke fixture (kept for allowlist parity) |

Source of truth for the full sample set: [receipt-intelligence-n8n `samples/`](https://github.com/RoxanaTapia/receipt-intelligence-n8n/tree/main/samples). Keep `05-demo-basket.pdf` (and its SHA-256 in `demo/app/sample.py`) in sync when the n8n fixture changes.

Compose mounts this directory into n8n at `/home/node/.n8n-files/samples` so the webhook can read the same bytes the visitor downloads.

Amounts on the sample PDF are labeled as demo currency (DC) — not EUR/USD.
