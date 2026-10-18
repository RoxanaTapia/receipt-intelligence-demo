# AGENTS.md — Receipt Intelligence Demo

Public notes for working in this repository.

This repo is the visitor UX and Compose packaging for a receipt-to-answers demo. Companion n8n workflows and API source live outside this repo; a walkthrough is available on request. This demo uses a hosted model.

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

## PR description standard

Roxana's rule since Oct 18, 2026: PR titles and descriptions are concise, consistent and easy to scan, so the PR history of the public repos tells a story. **This is the one standard for every unit**. Repos copy it as written. Also in `.github/pull_request_template.md`.

### PR title

- Format: `type(scope): what changes for the user`, lowercase, imperative, at most about 60 characters, with no issue number in the title.
- Types: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`. Scope is the area, for example `ui`, `api`, `deploy`.
- Example: `fix(ui): keep header fixed on mobile`
- PRs are squash-merged, so the PR title becomes the single commit on main and the main history reads as one line per change.

### PR body

```markdown
## 🎯 What
One or two lines on the user-visible change. Closes #184

## 🧱 Commit story
- fix(ui): pin header height before fonts load
- test(ui): add header position test at 390px and 1440px

## 🧪 Test
- [ ] CI green
- [ ] up to 3 checks that prove the fix

## 🚀 Deploy
`deploy-ai-doc` · rebuilds `app` · no env or config changes · rollback: revert plus redeploy

<details><summary>Details</summary>screenshots, numbers, longer notes</details>
```

- **Commit story:** each commit in the PR is one logical step with the same `type(scope): ...` style. No "wip" or "address review" commits; clean them up before review.
- **Deploy:** always the four items (exact script, services rebuilt, env or config changes, rollback). This repo has no named deploy script — write **No deploy** for docs-only PRs, or name real compose files under `deploy/` when the change needs a rebuild.
- **Double-check every command:** each command in a PR or review (deploy script, path, flag, test command) must be checked against the repo or the installed script before posting. Use only real names; never invent flags or paths. If a command could not be run or verified, say so in the PR.
- **Verified commands in this repo:**
  - Seed: `./deploy/seed-demo-data.sh`
  - Auth helper: `./deploy/generate-caddy-auth.sh <user> '<password>'` (needs Docker)
  - IP TLS helper: `./deploy/generate-ip-tls.sh <ipv4>` (needs `openssl`)
  - Demo tests: `pip install -r demo/requirements-dev.txt` then `python3 -m pytest demo/tests`
  - Compose (needs Docker): `docker compose --env-file .env -f deploy/docker-compose.yml config`
  - Issue read: `gh issue view NN` (no `#` in the shell argument)

### Review comment format

Every review comment is short, easy to scan, and uses emojis. Header line and at most five one-line bullets above a collapsed details block. Applies to code, deploy, live-test and copy reviews, and to the post-deploy OK.

```markdown
**✅ Pass · Deploy review (Nicky) · `abc1234`**  (or ❌ Fail)
- ✅ what works
- ❌ blocking issue
- ⚠️ minor, non-blocking
- 🚀 deploy notes
<details><summary>Details</summary>numbers, logs, screenshots</details>
```

### Public repos

Client-facing: no prices, hostnames, hosting provider, server sizes, `/root` paths, non-public repo links, internal notes, or Cursor agent badges and links in PR bodies.

## Commit & PR Policy

- Granular, reviewable commits (ideally 1–4 per issue), each `type(scope): ...`
- Follow the **PR description standard** and **Review comment format** above
- Human must approve before push or merge

## Review

Changes are reviewed and tested before merge.
