# Demo sample PDFs

Vendored allowlisted fixtures for the visitor **download → upload → ingest** path.

| File | n8n sample id | Role |
|------|---------------|------|
| [03-small.pdf](03-small.pdf) | `03-small` | Primary demo sample (smoke / portfolio) |

Source of truth for the full sample set: [receipt-intelligence-n8n `samples/`](https://github.com/RoxanaTapia/receipt-intelligence-n8n/tree/main/samples). Keep `03-small.pdf` (and its SHA-256 in `demo/app/sample.py`) in sync when the n8n fixture changes.

Compose mounts this directory into n8n at `/home/node/.n8n-files/samples` so the webhook can read the same bytes the visitor downloads.
