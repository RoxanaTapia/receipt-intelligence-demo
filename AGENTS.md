# AGENTS.md — Receipt Intelligence Demo

Public notes for working in this repository.

This repo is the visitor UX and Compose packaging for a receipt-to-answers demo. Companion n8n workflows and API source are private; a walkthrough is available on request. This demo uses a hosted model.

## Layout

| Path | Role |
|------|------|
| [`README.md`](README.md) | Product overview and live demo |
| [`DEPLOYMENT.md`](DEPLOYMENT.md) | Operator deploy guide |
| [`demo/`](demo/) | Visitor UX (FastAPI + Jinja templates) |
| [`deploy/`](deploy/) | Docker Compose, Caddy overlays, seed script |
| [`docs/`](docs/) | Architecture and screenshot map |
| [`.env.example`](.env.example) | Env template (secrets stay out of git) |

Reference deploy pattern: [ai-doc-to-chat `deploy/`](https://github.com/RoxanaTapia/ai-doc-to-chat-pipeline/tree/main/deploy).

## Tests

From `demo/`:

```bash
pip install -r requirements-dev.txt
pytest
```

There is no CI in this repo yet. Run the tests locally before opening a pull request.

## Review

Changes are reviewed and tested before merge.
