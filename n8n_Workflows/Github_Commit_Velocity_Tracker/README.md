# GitHub Commit Velocity Tracker

Engineering velocity is a leading indicator. The pace at which a company's public repositories are pushed, starred, and expanded tends to move before the press release — a sustained acceleration in active repos often precedes a product launch, an SDK release, or a research milestone by weeks.

Institutional alternative data providers have long treated open-source telemetry — commit cadence, contributor counts, repo activity — as a tradeable signal that front-runs reported fundamentals. This workflow builds a lightweight version of that same idea on free infrastructure. Every Sunday it pulls the 10 most-recently-pushed public repositories for each of 7 AI watchlist companies, computes weekly velocity metrics, compares against the previous week's run, and asks Groq to classify the engineering momentum. The output is a structured markdown report showing which companies are accelerating, which are stable, and which are quietly slowing down.

---

## Watchlist

| Ticker | Company | GitHub Org |
|---|---|---|
| NVDA | NVIDIA | `NVIDIA` |
| AMD | AMD | `GPUOpen-Tools` |
| INTC | Intel | `intel` |
| GOOGL | Google | `google` |
| AAPL | Apple | `apple` |
| MSFT | Microsoft | `microsoft` |
| META | Meta | `facebookresearch` |

---

## How It Works

For each company the workflow fetches the 10 most recently pushed public repos from the GitHub REST API. From those it calculates:

- **Active repos** — repos pushed in the last 30 days
- **Total stars** — sum across top 10 repos
- **Top repo** — highest starred repo
- **Languages** — unique languages across repos

It then compares against the previous week's stored run to produce:

- **repos_delta** — change in active repo count week over week
- **velocity_direction** — `ACCELERATING` (delta > 2), `DECELERATING` (delta < -2), or `STABLE`
- **delta_pct** — percentage change

Groq then classifies each company on two axes:

**activity_classification** — how much engineering throughput the org is showing:
`HIGHLY_ACTIVE` · `ACTIVE` · `MODERATE` · `LOW_ACTIVITY`

**momentum_signal** — the direction of that activity:
`BUILDING` · `MAINTAINING` · `SLOWING` · `PIVOTING`

Each company also gets a `key_observation` (one sentence), `notable_repos` (1–2 repos worth watching), and a `risk_flag` boolean.

---

## Architecture

```
Cron Trigger (weekly, Sunday 06:00 UTC)
  +
Manual Webhook  GET /run-github-pipeline
  ↓
Fetch Watchlist
  ↓
7 parallel GitHub REST API fetches
  GET /orgs/{org}/repos?per_page=10&sort=pushed&type=public
  Authorization: Bearer $GITHUB_TOKEN
  ↓
Merge GitHub Results  (waitForAll, 7 inputs)
  ↓
Parse & Calculate Velocity
  ↓
Load Previous Run from Supabase
  ↓
Calculate Week-over-Week Delta
  ↓
Aggregate for Groq
  ↓
Groq: Activity Classifier  (llama-3.3-70b-versatile)
  ↓
Parse Groq Response
  ↓
Signal Assembler
  ↓
Upsert to Supabase  (conflict: ticker, run_week)
  ↓
Generate Report
  ↓
Store Report in Supabase
  ↓
Pipeline Response  (Content-Type: text/markdown)
```

---

## Report Structure

Every run produces a markdown report with six sections:

1. **Executive Summary** — companies tracked, accelerating, stable, decelerating, risk flags
2. **Engineering Velocity Rankings** — sorted by active repos; per-company velocity direction, delta, classification, momentum, observation, top repo, notable repos, risk flag
3. **Accelerating Companies** — companies where `velocity_direction = ACCELERATING`
4. **Risk Flags** — companies where `risk_flag = true`
5. **Week-over-Week Delta Table** — repos this week vs last week, delta, direction per company
6. **Language Landscape** — top languages detected per company

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | n8n (self-hosted) |
| Data source | GitHub REST API (free, authenticated PAT) |
| LLM | Groq — `llama-3.3-70b-versatile` via HTTP Request nodes |
| Storage | Supabase (PostgreSQL) |
| Output | Markdown report via webhook + archived in Supabase |

---

## Prerequisites

- n8n instance running (self-hosted, v1.x+)
- Supabase project
- Free GitHub Personal Access Token
- Groq API key — [console.groq.com](https://console.groq.com)

---

## Supabase Setup

Run `setup.sql` in the Supabase SQL Editor before the first run. It creates:

- `github_signals` — one row per company per week, unique on `(ticker, run_week)`
- `github_reports` — full markdown report archive per run
- Indexes on `ticker`, `velocity_direction`, `risk_flag`, `run_timestamp`

---

## Credentials

Set these as environment variables on the n8n host before starting n8n:

| Variable | Where to get it |
|---|---|
| `GITHUB_TOKEN` | github.com/settings/tokens → Generate new token (classic) → `public_repo` scope only |
| `SUPABASE_URL` | Supabase → Project Settings → API |
| `SUPABASE_KEY` | Supabase → Project Settings → API (anon key) |
| `GROQ_API_KEY` | console.groq.com → API Keys |
| `PIPELINE_SECRET` | Any random string you choose |

```bash
export GITHUB_TOKEN=your-github-pat
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_KEY=your-anon-key
export GROQ_API_KEY=your-groq-key
export PIPELINE_SECRET=your-secret
npx n8n
```

In the n8n UI, also create:
- A **Supabase** credential and bind it to the two Supabase nodes
- A **Header Auth** credential (`X-Pipeline-Secret` = your `PIPELINE_SECRET`) and bind it to the Manual Pipeline Webhook node

> The GitHub token is read via `$env.GITHUB_TOKEN` in the 7 fetch nodes — no n8n credential needed for it, just the env var.

---

## Import & Activate

1. n8n → **Workflows → Import from File** → select `workflow.json`
2. Open **Upsert to Supabase** → bind your Supabase credential
3. Open **Store Report in Supabase** → bind your Supabase credential
4. Open **Manual Pipeline Webhook** → bind your Header Auth credential
5. Save — leave inactive until you've done a manual test run

---

## First Run

```bash
curl -H "X-Pipeline-Secret: your-secret" \
  http://localhost:5678/webhook/run-github-pipeline
```

The full markdown report is returned directly in the response. The first run seeds Supabase and has no week-over-week comparison — every company shows `is_first_run: true` and `delta_pct: N/A`. Subsequent runs compute real deltas.

The Cron trigger runs automatically every Sunday at 06:00 UTC once activated.

---

## Known Limitations

- **Top 10 repos per org only** — companies with many repos show a partial picture.
- **Active repo count, not raw commit count** — a single highly active repo may not move the metric.
- **First run has no week-over-week comparison** — meaningful delta data starts from the second run.
- **GitHub token required** — unauthenticated calls are limited to 60 requests/hour, insufficient for 7 companies.

---

## Project Structure

```
github-commit-velocity-tracker/
├── workflow.json
├── setup.sql
└── README.md
```

---

## Sample Output

```
# GitHub Commit Velocity Tracker — Signal Report

**Run ID:** `a7c2e8f1-3b4d-4a9e-8f1c-2d3e4f5a6b7c`
**Generated:** 2026-06-15T06:08:44.120Z
**Period:** 2026-W24

---

## Executive Summary

| Metric | Value |
|---|---|
| Companies tracked | 7 |
| Accelerating | 2 |
| Stable | 4 |
| Decelerating | 1 |
| Risk flags | 1 |

---

## Engineering Velocity Rankings

### 1. NVIDIA (NVDA)

- **Velocity:** ACCELERATING (+31.2%)
- **Activity:** HIGHLY_ACTIVE
- **Momentum:** BUILDING
- **Active repos:** 21 | **Stars:** 48,320
- **Observation:** Significant surge in inference and world-model repos
  pushed in the past week, consistent with a pre-release acceleration.
- **Top repo:** TensorRT-LLM
- **Notable repos:** TensorRT-LLM, cuda-samples
- **Risk flag:** no

### 2. Microsoft (MSFT)

- **Velocity:** STABLE (+2.1%)
- **Activity:** HIGHLY_ACTIVE
- **Momentum:** MAINTAINING
- **Active repos:** 18 | **Stars:** 112,440
- **Observation:** Broad, steady engineering output across Azure, dotnet,
  and AI tooling repos with no unusual acceleration.
- **Top repo:** TypeScript
- **Notable repos:** TypeScript, vscode
- **Risk flag:** no

### 3. Meta (META)

- **Velocity:** ACCELERATING (+18.7%)
- **Activity:** ACTIVE
- **Momentum:** BUILDING
- **Active repos:** 14 | **Stars:** 89,210
- **Observation:** facebookresearch org showing elevated push activity
  concentrated in LLaMA and related inference tooling repos.
- **Top repo:** llama
- **Notable repos:** llama, faiss
- **Risk flag:** no

### 7. Intel (INTC)

- **Velocity:** DECELERATING (-22.4%)
- **Activity:** LOW_ACTIVITY
- **Momentum:** SLOWING
- **Active repos:** 5 | **Stars:** 9,840
- **Observation:** Marked decline in active repo pushes — fewer than half
  the count from last week. OneAPI activity has dropped significantly.
- **Top repo:** intel-extension-for-pytorch
- **Notable repos:** intel-extension-for-pytorch
- **Risk flag:** ⚠️ YES

---

## Accelerating Companies

- **NVIDIA (NVDA)** — +31.2%, HIGHLY_ACTIVE — Pre-release acceleration
  in inference and world-model repos.
- **Meta (META)** — +18.7%, ACTIVE — Elevated activity in LLaMA and
  inference tooling.

---

## Risk Flags

- ⚠️ **Intel (INTC)** — SLOWING — Active repo count dropped 22.4% WoW.
  OneAPI activity significantly reduced.

---

## Week-over-Week Delta Table

| Company | Ticker | Repos (this week) | Repos (last week) | Delta | Direction |
|---|---|---|---|---|---|
| NVIDIA | NVDA | 21 | 16 | +5 | ACCELERATING |
| Microsoft | MSFT | 18 | 17 | +1 | STABLE |
| Meta | META | 14 | 11 | +3 | ACCELERATING |
| Google | GOOGL | 17 | 17 | 0 | STABLE |
| Apple | AAPL | 8 | 8 | 0 | STABLE |
| AMD | AMD | 9 | 10 | -1 | STABLE |
| Intel | INTC | 5 | 11 | -6 | DECELERATING |

---

## Language Landscape

| Company | Top Languages |
|---|---|
| NVIDIA | C++, Python, CUDA, CMake |
| Microsoft | TypeScript, C#, Python, Go |
| Meta | Python, C++, Jupyter Notebook |
| Google | Python, Go, Java, TypeScript |
| Apple | Swift, C++, Python |
| AMD | C++, Python, CMake |
| Intel | Python, C++, CMake |
```

---

## Author

**Sahiti Nallamolu**

- LinkedIn: [linkedin.com/in/sahitinallamolu](https://www.linkedin.com/in/sahitinallamolu/)
- Humanitarians AI Fellow

---

*Stack: n8n + GitHub REST API + Groq (llama-3.3-70b-versatile) + Supabase*

---