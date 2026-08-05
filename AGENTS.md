# AGENTS.md — Receipt Intelligence Demo

How we use Cursor agents, rules, and commands in this repository.

## Project Vision

**Delivery umbrella** for the Receipt Intelligence System: run n8n + API together on a VPS with a shared receipts volume, HTTPS/basic auth, and a thin self-serve demo UX visitors can try without opening the n8n editor.

**Stack:** Docker Compose · Caddy · thin demo UX · Hetzner VPS

Product logic stays in the sibling repos. This repo owns **glue + deploy + visitor UX**.

| Sibling | Role |
|---------|------|
| [receipt-intelligence-n8n](https://github.com/RoxanaTapia/receipt-intelligence-n8n) | Writes categorized JSON to disk |
| [receipt-intelligence-api](https://github.com/RoxanaTapia/receipt-intelligence-api) | Reads `RECEIPT_DATA_PATH`; analytics + Q&A |

## Project references

Agents use generic language; this table maps terms to **this repo**. Paths appear as work lands — do not invent placeholder trees.

| Term | Path |
|------|------|
| Compose / Caddy / scripts | `deploy/` (`deploy/docker-compose.yml`) |
| Env template | `.env.example` |
| Operator deploy guide | `DEPLOYMENT.md` (owned by #2) |
| Demo UX app | `demo/` (FastAPI + Jinja templates) |
| Seed / smoke | `demo/seed/`, `deploy/seed-demo-data.sh`, [DEPLOYMENT.md](DEPLOYMENT.md) + [README](README.md) local smoke |
| Portfolio README polish | #4 |
| Upstream API Dockerfile | [api #25](https://github.com/RoxanaTapia/receipt-intelligence-api/issues/25) ✅ |
| Integration contract (read-only) | [n8n integration.md](https://github.com/RoxanaTapia/receipt-intelligence-n8n/blob/main/docs/integration.md) |
| Reference deploy pattern | [ai-doc-to-chat `deploy/`](https://github.com/RoxanaTapia/ai-doc-to-chat-pipeline/tree/main/deploy) |

## Current Focus

- **Module 7 — Delivery** (this repo owns it)
- **Ship order:** [#1](https://github.com/RoxanaTapia/receipt-intelligence-demo/issues/1) Compose → [#2](https://github.com/RoxanaTapia/receipt-intelligence-demo/issues/2) Caddy + `DEPLOYMENT.md` → [#3](https://github.com/RoxanaTapia/receipt-intelligence-demo/issues/3) Demo UX v1 → [#4](https://github.com/RoxanaTapia/receipt-intelligence-demo/issues/4) README polish → [#5](https://github.com/RoxanaTapia/receipt-intelligence-demo/issues/5) live PDF later
- **Do not** change n8n or API product logic here — open PRs in those repos if needed

## Core Principles

- Keep things simple, readable, and maintainable
- Small, focused functions and changes
- One issue → one branch → one PR
- Prefer real deploy paths over shim stubs (mirror ai-doc `deploy/` layout)
- Secrets stay out of git (`.env.example` only)

## Agent Roster

| Role | Responsibility | Notes |
|------|----------------|-------|
| `milestone-orchestrator` | Coordinates shipping, branches, commits | Only agent allowed to commit |
| `deploy-engineer` | Compose, Caddy, volumes, networking, `.env.example`, Hetzner infra docs | Primary for #1, #2 |
| `demo-ux-engineer` | Thin visitor UI + seed/smoke + live sample ingest wiring | Primary for #3, #5 |
| `docs-writer` | README, `DEPLOYMENT.md`, `docs/` | `/document`; portfolio prose for #4 |
| `verifier` | Quality checks and acceptance criteria before PR | `/verify` |
| `software-engineering-professor` | Teaches issues; portable deploy/demo mental models | `/lecture-on-issue`; does not ship |

**Intentionally omitted** (live in sibling repos): `n8n-engineer`, `fastapi-engineer`, `claude-prompt-engineer`.

## Issue → agent map (Module 7)

| Issue | Primary | Secondary |
|-------|---------|-----------|
| #1 Compose stack | `deploy-engineer` | `docs-writer` (README pointers) |
| #2 Caddy + `DEPLOYMENT.md` | `deploy-engineer` | `docs-writer` |
| #3 Demo UX v1 + seed | `demo-ux-engineer` | `deploy-engineer` (Compose service) |
| #4 README first paint | `docs-writer` | — |
| #5 Live PDF (download → upload → ingest) | `demo-ux-engineer` | `deploy-engineer` (webhook URL / samples mount) |
| #18 Harden live ingest /n8n access | `demo-ux-engineer` + `deploy-engineer` | n8n subdomain + `N8N_PATH=/` (ai-doc Caddy) |

## Workflow

1. Pick a GitHub issue on the [Project board](https://github.com/users/RoxanaTapia/projects/3).
2. *(Optional)* `/lecture-on-issue #NN` — learn before building.
3. `/ship-issue #NN` — orchestrator implements with specialist support.
4. Inside shipping: run **`/document`** only if the issue creates or updates documentation; otherwise skip and note in the PR → always run **`/verify`** → PR with test plan from acceptance criteria.
5. Human reviews PR test plan and approves before push or merge.
6. After merge: **`/ship-complete #NN`** — tick acceptance criteria checkboxes on the issue.

Project **Status** uses GitHub Project automations (PR linked → In Progress; merged → Done).

## Slash Commands

| Command | Purpose |
|---------|---------|
| `/ship-issue` | Ship one GitHub issue end-to-end |
| `/document` | Run docs-writer review |
| `/verify` | Quality verification and acceptance criteria coverage before PR |
| `/ship-complete` | After merge — tick issue acceptance criteria checkboxes |
| `/lecture-on-issue` | Teach an issue (learner mode) |

## Rules

| Rule | Scope |
|------|-------|
| `.cursor/rules/documentation.mdc` | Markdown doc style |
| `.cursor/rules/elegant-minimal-python.mdc` | Python (demo UX) |

**When to call specialists:** `.cursor/agents/milestone-orchestrator.md`

**Documentation process:** `.cursor/agents/docs-writer.md`

## Commit & PR Policy

- Granular, reviewable commits (ideally 1–4 per issue)
- Only `milestone-orchestrator` creates commits
- **PR titles must not include issue numbers.** Use `Closes #NN` in the PR body.
- Run **`/document`** only if the issue creates or updates documentation; always run **`/verify`** before opening a PR
- PR description starts with a **Main contribution** paragraph
- Human must approve before push or merge

## Notes for Cursor

Read this file at the start of a new agent chat. Open **this repo** as the workspace root for `/ship-issue`.
