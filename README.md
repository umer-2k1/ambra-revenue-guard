# Ambra — Denial-to-Prevention Feedback Loop

> A working proof-of-concept that turns every **resolved** EMS insurance denial into a **reusable prevention rule**, and uses those rules to catch documentation gaps **before** a claim is submitted.

---

## Table of contents
1. [Abstract](#abstract)
2. [The problem](#the-problem)
3. [The solution](#the-solution)
4. [Who this is for](#who-this-is-for)
5. [The demo (4 screens)](#the-demo-4-screens)
6. [How it works (pipeline)](#how-it-works-pipeline)
7. [Architecture](#architecture)
8. [Tech stack](#tech-stack)
9. [AI providers (switchable)](#ai-providers-switchable)
10. [The data](#the-data)
11. [Scoring logic](#scoring-logic)
12. [API reference](#api-reference)
13. [Project structure](#project-structure)
14. [Getting started](#getting-started)
15. [Configuration](#configuration)
16. [Deploying (Vercel)](#deploying-vercel--two-projects-one-repo)
17. [Testing](#testing)
18. [Design system](#design-system)
19. [What this is NOT](#what-this-is-not)
20. [Roadmap](#roadmap)
21. [Glossary](#glossary)

---

## Abstract

Ambra911 runs two AI products for EMS (ambulance) agencies: **Scribe** (turns a voice report into a billing-ready claim) and **Denials** (fights denied claims with appeals). They work well — but they run as **separate pipelines**. When the Denials product *wins* an appeal, the lesson learned dies inside that one claim. Nothing flows back to prevent the next medic from making the same documentation mistake.

This project builds the missing link: a **feedback loop** that reads a history of resolved denials, uses an LLM to **extract reusable prevention rules**, stores them in **vector memory**, and then **scores every new claim** against that memory — flagging the exact documentation gaps that would get it denied, with a dollar estimate of the risk and a specific fix.

The result is a system that **gets smarter with every denial it resolves**: more denials resolved → more rules learned → fewer future denials.

It runs entirely on a laptop (or with a free Qdrant Cloud cluster), uses switchable AI providers (DeepSeek or Groq for reasoning; Google Gemini or Groq for embeddings), and is intentionally scoped as a **demo** — no login, no signup, no onboarding.

---

## The problem

Every ambulance agency stacks up resolved denials like this:

| | |
|---|---|
| **28** | resolved denial cases |
| **$36,570** | total denied |
| **5** | payers (UnitedHealthcare, Aetna, Anthem BCBS, Medicare, Cigna) |
| **71%** | later overturned on appeal |

**The knowledge is trapped.** When the appeal team wins a denial, it learns something valuable — *"UHC rejects ALS claims that never explain why a basic crew wasn't enough."* But that lesson lives and dies inside one claim file. It never reaches the next medic writing a chart. So the **same documentation gaps cause the same denials, over and over**, and every one costs staff time, calls, and weeks of waiting.

This is the gap between **charting** and **denial management** — two pipelines that never talk.

---

## The solution

A closed loop with four steps:

```
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   ▼                                                              │
 ① INGEST          ② ANALYZE              ③ REMEMBER       ④ PREVENT
 resolved         cluster + extract       store rules      score new claims
 denials    ──►   prevention rules   ──►  in vector   ──►  before submission
 (SQLite)         (LLM)                   memory           (LLM + retrieval)
                  + embeddings            (Qdrant)               │
   ▲                                                             │
   └──────────────── more denials resolved ──────────────────────┘
                    (the flywheel keeps turning)
```

1. **Ingest** — every resolved denial case (payer, denial code, what the crew wrote, what was missing, how it was appealed, the outcome, the money).
2. **Analyze** — cluster similar denials, send each cluster to an LLM, and extract **one prevention rule** per pattern (what went wrong + what documentation would have prevented it).
3. **Remember** — store rules as structured rows (SQLite) **and** as semantic embeddings (Qdrant), so they can be matched by *meaning*, not just keywords.
4. **Prevent** — when a new claim is drafted, retrieve the matching rules and **score the claim**, returning a risk level, the specific missing elements, a dollar estimate, and a plain-English fix.

---

## Who this is for

- **EMS billing & compliance teams** — see the payer-specific rules hiding in your own denial history.
- **Founders / investors / judges (non-technical)** — every screen leads with plain English; the code-level jargon sits behind hover tags or an expandable "details for billing teams" section.

The app is built for **both audiences at once**: a plain headline for everyone, and the real industry codes (`A0427`, `CO-16`, `ALS-1`) available for the experts.

---

## The demo (4 screens)

A ~4-minute walkthrough, left to right:

### 1 · Denials — *"here's the pile of resolved cases"*
28 cases in a table with summary stats (28 cases · $36,570 denied · 5 payers · 71% recovered). **Click any row** to open its full **case file**.

### 2 · Analyze — *"watch the system learn"*
Click **Analyze Denials**. The system clusters the cases, calls the LLM per cluster, and streams progress live over Server-Sent Events:

```
  0%  starting    Loaded 28 denial cases
 10%  clustering  Identified 5 denial patterns
 10%  extracting  Cluster 1/5: uhc_medical_necessity (6 cases)
 24%  stored      R-001  Document ALS necessity and why BLS/other transport was unsafe   [high, 95%]
 …
100%  complete    5 rules learned · 24 denial embeddings · 5 rule embeddings stored
```

### 3 · Knowledge Base — *"this is the system's memory"*
Each learned rule is a card: a **plain-English headline**, a plain "why this matters" line, "what to add to the chart", the real codes (hover for meaning), and the denials that taught it (click to open the case file). Technical details collapse into a **"details for billing teams"** section.

### 4 · Score Claim — *"the main event"*
A pre-filled PCR narrative is scored against the learned rules. Result:

```
HIGH  ·  93/100  ·  3 issues found · 5 rules checked
Top recommendation: … (for billing teams)
FOR NON-TECHS: The report says the patient had chest pain and got aspirin, but it
never explains why a paramedic was needed or what advanced care was actually given…

FLAG 1 [HIGH]  State ALS necessity and why BLS/other transport was unsafe   rule R-001 · 6 similar denials · est. $1,850
FLAG 2 [HIGH]  Document the ALS procedures actually performed              rule R-005 · 4 similar denials · est. $1,825
```

This claim *looks* fine. The system catches it before submission — and explains **why** in language anyone can follow.

---

## How it works (pipeline)

### Extraction agent (LangGraph workflow)
```
START → identify → process_cluster (per-cluster loop) → finalize → END
```
- **identify** groups the seed denials into clusters and emits opening progress events.
- **process_cluster** handles one cluster per step: call the LLM (with a single retry), then store the rule + embeddings. Loops until every cluster is done (sequential, so the live feed stays readable).
- **finalize** emits the completion event with final counts.

Progress is pushed through LangGraph's custom stream writer, so the SSE endpoint is a thin `async for` over `graph.astream(stream_mode="custom")`.

### Stack of the request path
```
React (Vite dev server, :5173)
   │  fetch + ReadableStream (SSE)  →  /api/*  (proxied to :8000)
   ▼
FastAPI (:8000)
   ├── SQLite  (denial_cases, prevention_rules, claim_scores)
   └── Qdrant  (denial_narratives, rule_embeddings)  ← Cloud or local embedded
          ▲
          │ embeddings (768-dim) via Gemini or Groq
   LLM  (DeepSeek or Groq) for extraction + scoring
```

---

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                        │
│   Denials  ·  Analyze (SSE live feed)  ·  Knowledge Base  ·  Score │
│   + case-file drawer   +  glossary drawer                      │
└──────────────────────────┬────────────────────────────────────┘
                           │ HTTP / SSE
┌──────────────────────────┴────────────────────────────────────┐
│                       BACKEND (FastAPI)                        │
│                                                                │
│   Extraction agent (LangGraph)      Scoring agent             │
│    cluster → LLM → store             retrieval + LLM + guard   │
│                                                                │
│   SQLite (structured)               Qdrant (semantic)         │
│    denial_cases                      denial_narratives        │
│    prevention_rules                  rule_embeddings          │
│    claim_scores                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Tech stack

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | **Python 3.13 + FastAPI** | fast, async, first-class SSE streaming |
| Agent workflow | **LangGraph** | explicit, streamable extraction graph with a retry edge |
| LLM access | **LangChain `ChatOpenAI`** | one client works with DeepSeek **and** Groq (OpenAI-compatible) |
| Structured DB | **SQLite** | zero-config, single file |
| Vector DB | **Qdrant** | local embedded (zero setup) **or** Qdrant Cloud |
| Embeddings | **Gemini** `gemini-embedding-001` (768-d) **or** **Groq** `nomic-embed-text-v1_5` (768-d) | switchable, both 768-dim |
| Frontend | **React 19 + Vite** | fast dev, component model |
| Styling | **Tailwind CSS v4 + shadcn/ui** | accessible primitives, used heavily |
| Package manager | **pnpm** (frontend) | fast, disk-efficient |
| Streaming | **Server-Sent Events** | real-time analysis progress |

---

## AI providers (switchable)

Two independent switches, both via `.env`:

**LLM** (`LLM_PROVIDER`)
- `deepseek` (default) — `deepseek-chat` / `deepseek-flash`, OpenAI-compatible API, paid but very cheap.
- `groq` — e.g. `llama-3.3-70b-versatile`, OpenAI-compatible, generous free tier.

**Embeddings** (`EMBEDDING_PROVIDER`)
- `gemini` (default) — `gemini-embedding-001`, 768-dim, free tier.
- `groq` — `nomic-embed-text-v1_5`, 768-dim, free tier.

Both providers are OpenAI-compatible and return 768-dim vectors, so switching is a one-line change with no code edits.

---

## The data

### Seed denials (28 cases)
Five real denial patterns plus four scattered one-offs (which the system correctly ignores):

| Cluster | Payer | Root cause | Cases |
|---|---|---|---|
| `uhc_medical_necessity` | UnitedHealthcare | Missing transport-necessity / "why not BLS" language | D-001…D-006 |
| `aetna_prior_auth` | Aetna | No prior authorization on scheduled non-emergency trips | D-007…D-011 |
| `anthem_mileage` | Anthem BCBS | Loaded mileage / destination not justified | D-012…D-015 |
| `medicare_documentation` | Medicare (Novitas) | Missing/expired PCS, condition codes | D-016…D-020 |
| `cigna_level_of_service` | Cigna | ALS level not supported by documented interventions | D-021…D-024 |
| *(scattered)* | mixed | timely filing, duplicate, etc. (skipped) | D-025…D-028 |

The data follows real US EMS-billing conventions: HCPCS ambulance codes (A0425–A0434), CARC/RARC denial codes (CO-16, CO-50, CO-197…), Medicare **PCS** rules and **condition codes P1–P7**, and origin/destination modifiers (`SH`). See `backend/data/seed_denials.json`.

### Case file (per denial)
Beyond the raw record, every case carries a full **case file** (generated by `scripts/enrich_seed.py` from each case's own dates, amounts, and appeal strategy):

- **`timeline`** — claim → denial → appeal → resolution, with real dates
- **`appeal_letter`** — the actual appeal that was sent
- **`payer_notes`** — call / portal / remittance follow-ups

### Prevention rules
Each rule stores a **plain-English** headline and summary (for non-experts) alongside the **technical** fields (for billing teams), plus the source denials, confidence, severity, and average denied amount.

---

## Scoring logic

Given a new claim:

1. **Soft retrieval** — union of:
   - vector similarity over **all** rules (semantic candidates), and
   - deterministic **payer/CPT** matches ("always look at these").
   This means a claim is checked against cross-payer rules describing the same failure mode, and a targeted rule can never be missed just because an embedding drifted.
2. **LLM judgement** — the claim + matched rules go to the LLM, which returns flags (missing element, suggestion, estimated risk) and a recommendation.
3. **Deterministic guard** — the overall risk can never be *lower* than what the flags imply, and the score is floored for HIGH/MEDIUM. **Nothing is fabricated** — flags only ever come from the model and only reference rules that were actually retrieved.
4. **Two audiences** — the recommendation is returned twice: the expert version, and a plain-English **"for non-techs"** version.

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/denials` | All 28 denial cases (with full case files) |
| GET | `/api/denials/stats` | Summary stats (total, $ denied, by payer / CARC / outcome) |
| POST | `/api/analyze` | Run analysis — returns an **SSE stream** of progress events |
| GET | `/api/rules` | All learned prevention rules |
| GET | `/api/rules/{rule_id}` | One rule |
| GET | `/api/demo-claim` | The pre-filled demo claim (Screen 4) |
| POST | `/api/score` | Score a claim narrative against the learned rules |
| GET | `/api/status` | System status (counts, providers, vector store mode) |
| POST | `/api/reset` | Clear rules, scores, and embeddings (keeps seed cases) |

Interactive docs: `http://localhost:8000/docs`.

---

## Project structure

```
.
├── backend/                     # ← its own Vercel project (Root Directory = backend)
│   ├── api/index.py            # Vercel Python entrypoint (exposes the FastAPI app)
│   ├── vercel.json             # function config (maxDuration, includeFiles)
│   ├── data/seed_denials.json  # 28 seed cases (with case files) — ships with the function
│   ├── requirements.txt
│   ├── main.py                 # FastAPI app + endpoints
│   ├── config.py               # provider switches + paths (relative to backend/)
│   ├── models.py               # Pydantic models
│   ├── database.py             # Postgres (Neon) or SQLite — schema, seed, queries
│   ├── embeddings.py           # Gemini / Groq embeddings (768-d)
│   ├── vector_store.py         # Qdrant (cloud or local), search, reset
│   ├── llm.py                  # LangChain ChatOpenAI wrapper
│   ├── prompts.py              # all LLM prompts
│   ├── extraction_agent.py     # LangGraph extraction workflow
│   ├── scoring_agent.py        # retrieval + scoring + guard
│   ├── demo_claim.py           # the Screen-4 demo narrative
│   └── test_*.py               # offline smoke tests
├── frontend/                    # ← its own Vercel project (Root Directory = frontend)
│   ├── src/
│   │   ├── App.jsx             # shell, tabs, drawers, status polling
│   │   ├── api.js              # API client (VITE_API_BASE_URL + SSE parsing)
│   │   ├── components/         # the 4 screens + drawers
│   │   │   └── ui/             # shadcn/ui components
│   │   └── lib/glossary.js     # plain-English meanings for codes
│   ├── package.json
│   └── vite.config.js
├── scripts/                     # enrich_seed.py, migrate_sqlite_to_postgres.py
├── docs/                        # spec + wireframes
├── .env.example
└── README.md
```

---

## Getting started

### Prerequisites
- Python **3.13+**
- Node **20+** with **pnpm** (`corepack enable pnpm`)
- API keys (see below)

### 1. Clone & configure
```bash
git clone <your-repo-url> ambra-revenue-guard
cd ambra-revenue-guard
cp .env.example .env      # then fill in your keys
```

### 2. Backend
```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cd backend && ../.venv/bin/uvicorn main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
pnpm install
pnpm dev        # http://localhost:5173
```

### 4. Use it
Open `http://localhost:5173`, then: **Denials** → **Analyze** → **Knowledge Base** → **Score Claim**.

> Before recording or demoing, hit **/api/reset** (or the "Reset & re-analyze" button) to start from a clean slate.

---

## Configuration

All configuration lives in `.env` (gitignored). Copy from `.env.example`.

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `deepseek` | `deepseek` \| `groq` |
| `DEEPSEEK_API_KEY` | — | required if `LLM_PROVIDER=deepseek` |
| `GROQ_API_KEY` | — | required for `groq` (LLM and/or embeddings) |
| `EMBEDDING_PROVIDER` | `gemini` | `gemini` \| `groq` |
| `GEMINI_API_KEY` | — | required if `EMBEDDING_PROVIDER=gemini` |
| `EMBEDDING_DIM` | `768` | vector size (must match Qdrant collections) |
| `QDRANT_URL` | *(empty)* | set to use **Qdrant Cloud / a server**; empty = **local embedded** |
| `QDRANT_API_KEY` | — | required when `QDRANT_URL` is set |
| `DATABASE_URL` | *(empty)* | Postgres (Neon) when set; empty = local SQLite |
| `DATABASE_PATH` | `backend/data/ambra_demo.db` | SQLite file (when no `DATABASE_URL`) |
| `QDRANT_PATH` | `backend/data/qdrant_db` | local Qdrant storage (when no `QDRANT_URL`) |
| `CORS_ORIGINS` | `http://localhost:5173,...` | comma-separated allowed browser origins |

**Minimum setup:** DeepSeek + Gemini (2 keys). **Single-key option:** set both providers to `groq` and use one Groq key.

---

## Deploying (Vercel — two projects, one repo)

The frontend and backend deploy as **two separate Vercel projects**, both connected to this same GitHub repo and told apart by their **Root Directory**.

**Prerequisites:** a **Qdrant Cloud** cluster (free 1 GB) and a **Neon Postgres** database (free, via Vercel's Storage tab).

### 1. Backend project
- New Vercel project → import this repo → **Root Directory = `backend`**.
- `vercel.json` already sets the function **`maxDuration: 300s`** (analysis streams ~90s) and ships `data/**`.
- Add these **Environment Variables**:

| Variable | Value |
|---|---|
| `LLM_PROVIDER` | `deepseek` (or `groq`) |
| `DEEPSEEK_API_KEY` | your DeepSeek key |
| `EMBEDDING_PROVIDER` | `gemini` (or `groq`) |
| `GEMINI_API_KEY` | your Gemini key |
| `QDRANT_URL` | your Qdrant Cloud endpoint |
| `QDRANT_API_KEY` | your Qdrant Cloud key |
| `DATABASE_URL` | Neon **pooled** connection string (`?sslmode=require`) |
| `CORS_ORIGINS` | your frontend URL (set in step 3) |

### 2. Frontend project
- New Vercel project → same repo → **Root Directory = `frontend`** (Vite is auto-detected; output `dist`).
- Env var: **`VITE_API_BASE_URL`** = the backend's URL, e.g. `https://ambra-api.vercel.app`.

### 3. Wire them together
1. Deploy the **backend** first → copy its URL.
2. Set the frontend's `VITE_API_BASE_URL` to that URL → redeploy the frontend.
3. Set the backend's `CORS_ORIGINS` to the frontend's URL → redeploy the backend.

### Notes
- **Qdrant must be Cloud** (or a server) on Vercel — the embedded local mode is file-based and won't work serverless.
- **`DATABASE_URL` is required** in the cloud — there's no persistent disk for SQLite. (Leave it unset locally and the app uses SQLite automatically.)
- **Vercel Hobby** is licensed for personal/non-commercial use.
- This app is **single-user by design** — `/api/analyze` and `/api/reset` mutate shared state.

---

## Testing

Offline smoke tests (no API keys required — the LLM and embeddings are stubbed):

```bash
.venv/bin/python backend/test_data.py         # seed load, clustering, empty store
.venv/bin/python backend/test_extraction.py   # LangGraph workflow end-to-end (stubbed)
.venv/bin/python backend/test_scoring.py      # retrieval + normalization guard
```

---

## Design system

Ambra's warm palette, applied through shadcn/ui tokens:

| Token | Value | Use |
|---|---|---|
| `--primary` | `#5C0A05` | dark brown-red — headings, primary buttons |
| `--accent` | `#FE4311` | orange — metrics, highlights |
| `--background` | `#F8F4F1` | warm off-white |
| `--secondary` | `#EEE7DE` | beige cards |
| `--border` | `#DBD0C2` | warm tan |
| risk high / med / low | `#DC2626` / `#F59E0B` / `#10B981` | risk badges |

Buttons are pill-shaped; cards are ~16px radius; no harsh shadows. Font: Inter.

---

## What this is NOT

- **Not** a replacement for Ambra's existing products (appeal letters, IVR agent, NEMSIS validation, claim statusing).
- **Not** a deployed production system — it runs locally (or against a free Qdrant Cloud cluster).
- **Not** a full app — deliberately **no login, signup, or onboarding**.
- **Not** a live data feed — analysis is triggered on demand and streams in real time during the demo.

---

## Roadmap

- Track time saved and dollars recovered as an explicit KPI.
- Feed new resolved denials back in automatically (close the loop in production).
- Link each rule directly to the denials that produced it (partially done: "taught by" chips).
- Plain-English versions for every flag (not just the top recommendation).
- One-command startup (`start.sh`) + a recorded Loom walkthrough.

---

## Glossary

| Term | Meaning |
|---|---|
| **ALS** | Advanced Life Support — paramedic-level care. |
| **BLS** | Basic Life Support — EMT-level care. |
| **PCR** | Patient Care Report — the run sheet a crew writes. |
| **POV** | Privately Owned Vehicle — a personal car. |
| **PCS** | Physician Certification Statement — a doctor's signed note of medical necessity. |
| **CARC / RARC** | The payer's standard codes explaining a denial. |
| **CPT** | The billing code for a service (e.g. `A0427` = ALS-1 emergency). |
| **A0425 / 27 / 28 / 29 / 33 / 34** | Ambulance transport HCPCS codes by level & emergency status. |

*(The same glossary is built into the app — click **Glossary** in the header.)*

---

<p align="center"><em>Every resolved denial makes the system smarter. Connect charting and denial management, and denial rates fall over time.</em></p>
