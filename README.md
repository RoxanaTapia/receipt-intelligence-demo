# Receipt Intelligence

> Use the sample receipt, see a category on every line, and ask spend questions in plain language.

> **Takeaway:** This is a receipt-to-answers pipeline, not a chatbot that guesses a budget. If the receipts do not contain the spend, it says so.

## What it is

You read a sample receipt on the page. Each line gets a category. You ask a spending question in plain language, and the totals are calculated from the receipts on the page. If those receipts do not contain the spend, the demo says so.

The merchants are fictional. Amounts on the page are demo figures. This is not for your real receipts.

## What works now

| What you can do | In practice |
|-----------------|-------------|
| **Sample receipt** | Read Green Basket Market on the page. The seeded receipts are already there |
| **Line-item categories** | You get a category on every line, not a single merchant guess |
| **Spending answers** | Totals are calculated from the receipts on the page |
| **Plain-language Q&A** | Ask "How much did I spend per category?" |
| **Self-serve** | You do not open an n8n editor. The browser never talks to n8n |

## How to try it

🟢 **Live** · <a href="https://receipt-intelligence.roxanatapia.dev/try/website" target="_blank" rel="noopener noreferrer"><strong>receipt-intelligence.roxanatapia.dev</strong></a>

▶ **[Watch the demo](https://youtu.be/q03q0kfvTfQ)**

- Open the live demo. Corner Studio, a fictional studio, asks where the snack money went
- Read Green Basket Market on the page and watch a category appear on each line
- Ask where the snacks went. The total is calculated from the receipts on the page
- A walkthrough is available on request. [Ask on Upwork](https://www.upwork.com/freelancers/roxanadev) or [contact me](https://roxanatapia.dev/#contact)

## Where things live

This repository holds the visitor UI and the deployment setup.

| Path | What it holds |
|------|----------------|
| [`demo/`](demo/) | Visitor UI (FastAPI and Jinja templates) |
| [`demo/seed/`](demo/seed/) | Fictional receipts already on the page |
| [`deploy/`](deploy/) | Deployment files |
| [`docs/`](docs/) | Architecture notes and the screenshot map |

<span id="how-it-fits-together"></span>

Reading the receipt happens in n8n workflows that live in their own repository. Totals and answers come from a FastAPI service that lives in its own repository.

Repo map: [docs/README.md](docs/README.md). Deploy picture: [docs/product/architecture.md](docs/product/architecture.md). Operator steps: [DEPLOYMENT.md](DEPLOYMENT.md).

## Automated tests

The visitor demo has 118 automated tests. The [Automatic tests pass](https://github.com/RoxanaTapia/receipt-intelligence-demo/actions/runs/46001884904) run on main, commit `ab8117d`, reported 118 passed. GitHub Actions runs that workflow on every pull request and on every push to main ([`.github/workflows/tests.yml`](.github/workflows/tests.yml)), and checks that the vendored demo kit still matches its checksum. The tests cover the visitor demo only.

## How I work with AI

I build with AI coding agents. Every change goes through a pull request I review and merge, with automated tests you can see on every change.

---

[Roxana Tapia](https://github.com/RoxanaTapia) · [How I work with AI](docs/how-we-work.md) · [MIT License](LICENSE)
