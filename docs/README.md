# Documentation

## Background

This page is the map of the repository. The [root README](../README.md) is the product overview. Start here when you want to know where code lives and how a receipt becomes an answer.

> **Takeaway:** Visitor UX in `demo/`. Ops in `deploy/`.

---

## Where to find what

```text
.
├── README.md          Client overview and live demo
├── AGENTS.md          Tests, layout, and review note
├── DEPLOYMENT.md      Self-host and VPS notes
├── demo/              Visitor UI (FastAPI + Jinja)
├── deploy/            Docker, Compose, Caddy overlays
├── .cursor/           Coding and docs conventions
└── docs/              You are here
      product/         Architecture (what runs on the VM)
      screenshots/     60s Loom frames (1920×1080)
```

| Path | Open it for |
|------|-------------|
| [`demo/app/main.py`](../demo/app/main.py) | Sample download, live ingest, spending context, Q&A form |
| [`demo/app/n8n_client.py`](../demo/app/n8n_client.py) | UX → n8n ingest webhook (Compose network only) |
| [`demo/app/api_client.py`](../demo/app/api_client.py) | UX → analytics and questions API |
| [`demo/seed/`](../demo/seed/) | Fictional example receipts for the seeded path |
| [`demo/samples/`](../demo/samples/) | Allowlisted PDF the visitor downloads and uploads |
| [`deploy/`](../deploy/) | Compose stack. Shared-host Caddy follows the [ai-doc deploy pattern](https://github.com/RoxanaTapia/ai-doc-to-chat-pipeline/tree/main/deploy) |
| [`docs/product/architecture.md`](product/architecture.md) | What runs on the VM |
| [`docs/screenshots/`](screenshots/) | Before/after and storyboard frames for the visitor demo |
| [`DEPLOYMENT.md`](../DEPLOYMENT.md) | Firewall, `.env`, shared-host vs solo Caddy |
| [`AGENTS.md`](../AGENTS.md) | How to run tests and what lives where |

---

## How a receipt becomes an answer

Two layers: the running services, then the steps that turn a PDF into a spend answer.

### Runtime

The browser never talks to n8n. Caddy terminates HTTPS and the invite gate. The demo UX calls n8n and the API on the private Docker network. n8n writes categorized JSON to a shared volume; the API reads that same folder.

Deploy picture and sequence: [product/architecture.md](product/architecture.md).

### Pipeline

| Stage | Where | Role |
|-------|-------|------|
| Ingest | n8n | Read the PDF. Fill a receipt schema. Categorize each line. |
| Validate | n8n | Schema and taxonomy checks, with a short retry. |
| Persist | shared volume | Canonical JSON. One store for writer and reader. |
| Analytics | API | Totals by date and category. Deterministic. |
| Answer | API | Route the question, then narrate those totals. |
| Show | `demo/` | Categories, spending bars, and the reply. |

Product steps in more detail: [README — How a receipt becomes an answer](../README.md#how-a-receipt-becomes-an-answer).

---

Self-host steps stay in [DEPLOYMENT.md](../DEPLOYMENT.md). Live demo: [receipt-intelligence.roxanatapia.dev](https://receipt-intelligence.roxanatapia.dev/).
