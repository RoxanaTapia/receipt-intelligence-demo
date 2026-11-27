# Project guide

## What we're building

This repo is the visitor page and the Compose packaging for a receipt demo. A visitor opens a sample receipt, sees a category on each line, and asks a spending question. Totals come from the receipts on the page. The page is FastAPI and Jinja templates. Companion workflows and the API live outside this repo. The demo uses a hosted model.

## How a change happens

1. **One issue.** The issue is the written request. Each request stays one piece of work. Use `.github/ISSUE_TEMPLATE.md`. The title starts with one emoji code, such as 🛠️ or 📄, then a short name.
2. **One branch.** The branch is a separate copy of the project, so this work does not mix with anything else. Its name is plain and descriptive, such as `agent-docs`.
3. **One pull request.** The pull request is the proposal to add that copy. The title is a plain sentence, with no type prefix and no emoji. The description uses `.github/pull_request_template.md`.
4. **Automated tests.** The tests run on every pull request and on every push to main.
5. **Roxana reviews and merges.** Roxana reviews every change, and she merges it.

## Where things are

| Path | What it is |
|------|------------|
| [README.md](README.md) | Product overview and the live demo |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Operator deploy guide |
| [demo/](demo/) | Visitor page, FastAPI and Jinja templates |
| [demo/tests/](demo/tests/) | Automated tests for that page |
| [demo/seed/](demo/seed/) | Fictional receipts already on the page |
| [deploy/](deploy/) | Docker Compose, Caddy overlays, and the seed script |
| [docs/](docs/) | Architecture notes and the screenshot map |
| [vendor/demo-kit/](vendor/demo-kit/) | Shared header, tokens, fonts, and icons. CI checks the checksum. |
| [.env.example](.env.example) | Env template. Secrets stay out of git. |
| [AGENTS.md](AGENTS.md) | This guide |
| [.cursor/rules/](.cursor/rules/) | Short rules for the agents |
| [.github/workflows/tests.yml](.github/workflows/tests.yml) | Runs the automated tests |
| [.github/ISSUE_TEMPLATE.md](.github/ISSUE_TEMPLATE.md) | The short form for a new issue |
| [.github/pull_request_template.md](.github/pull_request_template.md) | The short form for a pull request |
| [pyproject.toml](pyproject.toml) | Ruff settings for Python style |

## Tests

From the repo root:

```bash
pip install -r demo/requirements-dev.txt
python3 -m pytest demo/tests
ruff check
ruff format --check
```

GitHub Actions runs `ruff check`, `ruff format --check`, and pytest from `demo/` on every pull request and on every push to main. The workflow also checks the vendored demo kit hash.

## For the agents

Do:

- Read this guide and stay inside the current issue.
- Keep the visitor page behaviour the same unless the issue asks for a behaviour change.
- Prefer a small, clear change. Use `pathlib`, f-strings, and short docstrings.
- Run the tests above before the pull request is ready.
- Write public text in plain words, with real paths and real commands.

Don't:

- Don't merge. Roxana reviews and merges.
- Don't deploy. Roxana deploys.
- Don't weaken a test to make it pass.
- Don't reformat `vendor/demo-kit/`.
- Don't put secrets, prices, hostnames, or private repo links in public writing.
- Don't invent paths, flags, or numbers.
