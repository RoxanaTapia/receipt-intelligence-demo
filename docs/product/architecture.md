# Architecture

## Background

How the live demo runs on one machine. For the product pipeline and module map, see [docs/README.md](../README.md). For install steps, see [DEPLOYMENT.md](../../DEPLOYMENT.md).

> **Takeaway:** HTTPS at the edge. The browser never talks to n8n. n8n writes categorized JSON; the API reads that same folder.

---

## What runs where

n8n writes. The API reads. Claude extracts, categorizes, and narrates — it does not do the spend math.

```mermaid
flowchart TB
    User(["User"])

    subgraph VM["Single VM · Docker Compose"]
        Caddy["Caddy\nHTTPS + invite"]

        subgraph UX["Demo UX"]
            Upload["Sample PDF upload"]
            QA["Spending Q&A"]
        end

        n8n["n8n\nExtract + categorize"]
        API["API\nAnalytics + answer"]
        Disk[("Shared receipts JSON")]
        Claude["Claude"]
    end

    User <-->|HTTPS| Caddy
    Caddy --> Upload
    Upload --> n8n
    n8n --> Disk
    Caddy --> QA
    QA --> API
    API --> Disk
    n8n <--> Claude
    API <--> Claude
    QA --> Caddy

    classDef default fill:#f8fafc,stroke:#334155,stroke-width:1.5px,color:#0f172a
    classDef header fill:#e0f2fe,stroke:#0ea5e9,stroke-width:2px,color:#0f172a
    class User header
    class Caddy,Upload,QA,n8n,API,Disk,Claude default
```

| Piece | Role |
|-------|------|
| **Caddy** | HTTPS and the invite gate. Only ports 80 and 443 face the internet. On the portfolio VPS this process runs in [roxanatapia-edge](https://github.com/RoxanaTapia/roxanatapia-edge). |
| **Demo UX** | Sample download, live ingest, spending context, questions. This repo, [`demo/`](../../demo/). |
| **n8n** | Extract, categorize, validate, persist JSON. The browser never talks to it. |
| **API** | Deterministic totals, then a narrated answer from those numbers. |
| **Shared volume** | One store: n8n writes, the API reads. |
| **Claude** | Schema fill and categories in n8n; question routing and narration in the API. |

---

## One question

```mermaid
sequenceDiagram
  participant U as Browser
  participant X as Demo UX
  participant N as n8n
  participant A as API

  U->>X: Download sample PDF, upload it
  X->>N: Ingest webhook (allowlisted sample)
  N->>N: Extract, categorize, validate
  N->>N: Persist JSON on shared volume
  U->>X: Ask a spend question
  X->>A: Question
  A->>A: Route, aggregate, narrate
  A-->>X: Answer from those totals
  X-->>U: Categories, spending context, answer
```

---

## What this pilot does not include yet

A private archive, tax export, bank sync, or multi-user accounts. Those wait for a real engagement. The extract → persist → aggregate loop stays the same when they land.
