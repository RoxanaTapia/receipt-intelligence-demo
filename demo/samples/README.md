# Demo sample PDFs

Vendored allowlisted fixtures for the visitor **download → upload → ingest** path.

| File | n8n sample id | Role |
|------|---------------|------|
| [sample-supermarket-receipt.pdf](sample-supermarket-receipt.pdf) | `sample-supermarket-receipt` | **Primary** portfolio sample (Green Basket Market, 15 Aug 2026, DC) |
| [03-small.pdf](03-small.pdf) | `03-small` | Optional smoke fixture (kept for allowlist parity) |

Regenerate the supermarket PDF (and refresh `SAMPLE_SHA256` in [`../app/sample.py`](../app/sample.py)) with:

```bash
python3 demo/scripts/generate_sample_receipt.py
```

The script is deterministic (frozen PDF dates/IDs) so the hash stays stable.

Compose mounts this directory into n8n at `/home/node/.n8n-files/samples`. The webhook looks up `{sample id}.pdf` on that mount — the same bytes the visitor downloads.

Amounts are demo currency (DC) — not EUR/USD.

The **visitor allowlist in this repo** is the SHA-256 in `demo/app/sample.py`.
