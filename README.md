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

## Local compose smoke

Prerequisites: Docker (Compose v2), and the API sibling cloned next to this repo:

```text
<parent>/
├── receipt-intelligence-api
└── receipt-intelligence-demo   # this repo
```

```bash
cp .env.example .env
# set N8N_BASIC_AUTH_PASSWORD (and ANTHROPIC_API_KEY for Q&A / workflows)

./deploy/seed-demo-data.sh

docker compose --env-file .env -f deploy/docker-compose.yml up --build -d

curl -s http://localhost:8000/health
# {"status":"ok"}

curl -s http://localhost:8080/health
# {"status":"ok"}

# One question against seeded receipts (needs ANTHROPIC_API_KEY)
curl -s http://localhost:8000/questions \
  -H 'Content-Type: application/json' \
  -d '{"question":"How much did I spend on drinks in May 2026?"}'

# Optional: confirm n8n can reach the API on the Compose network
docker compose --env-file .env -f deploy/docker-compose.yml exec n8n \
  wget -qO- http://api:8000/health
```

| Service | Host URL |
|---------|----------|
| **Demo UX** | http://localhost:8080/ |
| API | http://localhost:8000/docs |
| n8n | http://localhost:5678 |

If host port `5678` or `8080` is already in use, set `N8N_HOST_PORT` / `UX_PORT` in `.env` before `up`.

Shared categorized JSON lives in `data/receipts/` (seed script + n8n writes; API reads via `RECEIPT_DATA_PATH=/data/receipts`). On the Compose network, n8n and the UX use `http://api:8000` (service DNS).

**Public portfolio path:** invite/Login at `https://receipt-intelligence.roxanatapia.dev/` → visitor UX under `/app` (see [DEPLOYMENT.md](DEPLOYMENT.md)).

VPS / HTTPS: [DEPLOYMENT.md](DEPLOYMENT.md). Product workflow import and sample PDFs: [n8n integration runbook](https://github.com/RoxanaTapia/receipt-intelligence-n8n/blob/main/docs/integration.md).
