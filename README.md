# Receipt Intelligence

> Use the sample receipt, see a category on every line, and ask spend questions in plain language.

> **Takeaway:** This is a receipt-to-answers pipeline, not a chatbot that guesses a budget. If the receipts do not contain the spend, it says so.

## Results

The demo app in this repository has [93 automated tests](https://github.com/RoxanaTapia/receipt-intelligence-demo/actions/runs/45682353883). GitHub Actions runs them on every pull request and on every push to main ([`.github/workflows/tests.yml`](.github/workflows/tests.yml)), and checks that the vendored demo kit still matches its checksum. The tests cover the visitor demo only.

## What works now

| What you can do | In practice |
|-----------------|-------------|
| **Sample receipt** | Tap a sample receipt on the page. Uploading a PDF is for a signed-in operator |
| **Line-item categories** | You get a category on every line, not a single merchant guess |
| **Spending answers** | Totals are calculated from the receipts on the page |
| **Plain-language Q&A** | Ask "How much did I spend per category?" |
| **Self-serve** | You do not open an n8n editor. The browser never talks to n8n. |

The merchants are fictional. Amounts on the page are demo figures. This is not for your real receipts.

## Where did August go?

Corner Studio, a fictional studio, asks one question. Where did the August snack money go?

Every amount in this section is sample data from the sample receipt only. That receipt is Green Basket Market, dated 15 August 2026, and the PDF labels it SAMPLE RECEIPT ([`demo/samples/sample-supermarket-receipt.pdf`](demo/samples/sample-supermarket-receipt.pdf)). The other fictional examples on the page are not part of these figures.

The sample prints butter croissants at 3.20 DC. The demo files that line as snacks. The same receipt prints a total of 25.00 DC. The categories are the ones stored with the sample in [`demo/app/sample_receipt.py`](demo/app/sample_receipt.py).

Sample data from the sample receipt only:

| Category | Lines printed on the sample | Sample data |
|----------|-----------------------------|-------------|
| Food | Bananas 1.20, baby spinach 2.40, whole milk 1.80, Greek yogurt 2.60, sourdough loaf 3.80 | 11.80 DC |
| Drinks | Orange juice 2.90, sparkling water 1.50 | 4.40 DC |
| Snacks | Butter croissants 3.20 | 3.20 DC |
| Household | Dish soap 2.50, paper towels 3.10 | 5.60 DC |

DC is demo currency, not real money. The amounts are the figures printed on each line. On this sample, August snacks are the croissants.

### One-minute steps

1. You tap a sample receipt.
2. Claude extracts the merchant, the date, and each line. n8n reads the PDF.
3. Each line gets a category. The record is checked, then saved as JSON.
4. FastAPI adds the totals in Python.
5. Claude explains those totals.

The automated tests that check these sample totals are linked from [Results](#results).

## How it fits together

Each step exists to keep your answer inside receipts that were actually ingested.

![1 Sample receipt. 2 Claude extracts. 3 Categorized and checked. 4 Saved as JSON. 5 FastAPI totals. 6 Claude explains.](docs/assets/receipt_architecture.png)

| Step | Technique | Why? |
|------|-----------|------|
| **Read** | n8n extracts text from the PDF | Receipts are layouts, not spreadsheets. |
| **Extract** | Claude fills a receipt schema (merchant, date, line items) | Downstream steps need structured fields, not prose. |
| **Categorize** | Each line gets a category from a fixed taxonomy | You can ask "How much did I spend per category?" Totals cross merchants. |
| **Validate** | Schema and taxonomy checks, with a short retry | Invalid JSON never becomes the answer. |
| **Persist** | Canonical JSON on a shared volume | One store: n8n writes, the API reads. |
| **Analytics** | FastAPI aggregates by date and category | Totals are calculated, not guessed. |
| **Answer** | This page totals the receipts you can see | The sentence uses those numbers. It says when the receipts do not contain the spend. |

n8n · FastAPI · Claude · Docker Compose

## What's planned

This is not accounting software yet. Tax export, bank sync, and multi-user accounts come later. Reading the receipt, saving it, and calculating the totals stay the same.

## Try it

🟢 **Live** · <a href="https://receipt-intelligence.roxanatapia.dev/" target="_blank" rel="noopener noreferrer"><strong>receipt-intelligence.roxanatapia.dev</strong></a>

▶ **[Watch the demo](https://youtu.be/q03q0kfvTfQ)**

- Request an invite on the gate, then redeem the code
- Tap a sample receipt on the demo page and watch the categories appear
- The examples already on the page stay available. Questions cover those examples plus the receipt you open in this session
- Uploading a file is for a signed-in operator
- A full-stack walkthrough is available on request. [Ask on Upwork](https://www.upwork.com/freelancers/roxanadev) or [contact me](https://roxanatapia.dev/#contact)

## Where things are

This repository is a portfolio demo of the visitor UI and the deployment setup.

| Path | What it holds |
|------|----------------|
| [`demo/`](demo/) | Visitor UI (FastAPI and Jinja templates) |
| [`deploy/`](deploy/) | Deployment files |
| [`docs/`](docs/) | Architecture notes and the screenshot map |

The extraction workflows and the API are not part of this repository.

Repo map: [docs/README.md](docs/README.md). Deploy picture: [docs/product/architecture.md](docs/product/architecture.md). Operator steps: [DEPLOYMENT.md](DEPLOYMENT.md).

---

[Roxana Tapia](https://github.com/RoxanaTapia) · [How I work with AI](docs/how-we-work.md) · [MIT License](LICENSE)
