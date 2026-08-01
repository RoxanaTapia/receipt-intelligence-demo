# receipt-intelligence-demo

Hetzner demo stack + self-serve UX for Receipt Intelligence (n8n + API). **Delivery Module 7.**

Product logic lives in the sibling repos; this umbrella owns Compose, Caddy/deploy docs, and the visitor demo UX.

| Repo | Role |
|------|------|
| [receipt-intelligence-n8n](https://github.com/RoxanaTapia/receipt-intelligence-n8n) | Ingest + categorization (writes receipts) |
| [receipt-intelligence-api](https://github.com/RoxanaTapia/receipt-intelligence-api) | Analytics + Q&A (reads receipts) |
| **This repo** | Run them together + public demo path |

## Agent workflow

Start with [`AGENTS.md`](AGENTS.md). Slash commands: `/lecture-on-issue`, `/ship-issue`, `/document`, `/verify`, `/ship-complete`.

**Ship order:** [#1](https://github.com/RoxanaTapia/receipt-intelligence-demo/issues/1) Compose → [#2](https://github.com/RoxanaTapia/receipt-intelligence-demo/issues/2) Caddy + `DEPLOYMENT.md` → [#3](https://github.com/RoxanaTapia/receipt-intelligence-demo/issues/3) Demo UX → [#4](https://github.com/RoxanaTapia/receipt-intelligence-demo/issues/4) README polish.
