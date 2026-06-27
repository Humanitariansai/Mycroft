# Research Footprint Monitor

A company's presence in AI research is a slow-moving but durable signal. The papers a company presents at NeurIPS or ICML today reflect research investments made 6–12 months ago — and point toward products 6–12 months out. At the same time, Wikipedia edit activity around a company is a fast-moving signal: edit spikes on a company's page typically precede mainstream news cycles by 24–72 hours, as editors react to events before coverage peaks.

The Research Footprint Monitor combines both. Every Monday it queries the Semantic Scholar API for recent papers authored by each watchlist company at the top AI research venues, and the Wikipedia MediaWiki API for edit velocity on each company's page over the last 7 days. The two signals are fused into a single `research_footprint_score` (0–100) per company, stored to Supabase, and returned as a structured markdown report.

Both APIs are completely free with no authentication required.

---

## The Two Signals

### Layer A — Semantic Scholar (6–12 month lag)

Queries the [Semantic Scholar Graph API](https://api.semanticscholar.org/) for papers from 2023 onwards matching each company. Measures:

- **Paper count** — volume of academic output
- **Conference presence** — papers at NeurIPS, ICML, CVPR, ICLR (the strongest proxy for frontier research investment)
- **Total and average citations** — a rough quality signal

Conference presence matters more than raw paper count. A company presenting at NeurIPS is competing at the field's leading edge, not just publishing.

### Layer B — Wikipedia (24–72 hour lead)

Queries the [Wikipedia MediaWiki API](https://www.mediawiki.org/wiki/API:Revisions) for page revisions over the last 7 days. Measures:

- **Edit count (7d)** and **edit velocity** (edits per day)
- **Unique editors** — breadth of attention vs. a single active editor
- **Spike flag** — more than 10 edits in a week

Edit spikes are a leading indicator. They typically precede mainstream news by 24–72 hours.

---

## Footprint Score (0–100)

`research_footprint_score = min(100, scholar_component + wikipedia_component)`

**Scholar component (max 60 pts)**

| Condition | Points |
|---|---|
| paper_count ≥ 8 | 30 |
| paper_count ≥ 4 | 20 |
| paper_count ≥ 1 | 10 |
| Has NeurIPS paper | +8 |
| Has ICML paper | +7 |
| Has CVPR paper | +5 |
| Has ICLR paper | +5 |
| avg_citations > 50 | +5 |

**Wikipedia component (max 40 pts)**

| Condition | Points |
|---|---|
| edit_count_7d ≥ 20 | 20 |
| edit_count_7d ≥ 10 | 15 |
| edit_count_7d ≥ 5 | 10 |
| Baseline | 5 |
| unique_editors ≥ 10 | +10 |
| unique_editors ≥ 5 | +5 |
| is_spike | +10 |

**Tiers**

| Score | Tier |
|---|---|
| ≥ 75 | DOMINANT |
| ≥ 50 | STRONG |
| ≥ 25 | PRESENT |
| < 25 | MINIMAL |

---

## Architecture

```
Cron Trigger (weekly, Monday 07:00 UTC)
  +
Manual Webhook  GET /run-research-pipeline
  ↓
Fetch Watchlist
  ↓
┌────────────────────────────────────────┐
│  LAYER A — Semantic Scholar (×7)       │
│  7 parallel HTTP Request nodes         │
│  GET api.semanticscholar.org/graph/v1  │
│    /paper/search?query={company}       │
│    &fields=title,authors,venue,year,   │
│      citationCount&limit=10&year=2023- │
│  No Authorization header               │
└────────────────────────────────────────┘
  ↓
Merge Scholar Results  (combineByPosition, 7 inputs)
  ↓
Parse Scholar Data

┌────────────────────────────────────────┐
│  LAYER B — Wikipedia (×7)              │
│  7 parallel HTTP Request nodes         │
│  GET en.wikipedia.org/w/api.php        │
│    ?action=query&prop=revisions        │
│    &titles={company}&rvlimit=50        │
│    &rvstart={7 days ago}&format=json   │
│  No Authorization header               │
└────────────────────────────────────────┘
  ↓
Merge Wikipedia Results  (combineByPosition, 7 inputs)
  ↓
Parse Wikipedia Data
  ↓
Combine Signals  (combineByPosition, 2 inputs)
  ↓
Calculate Footprint Scores
  ↓
Aggregate for Groq
  ↓
Groq: Footprint Analyst  (llama-3.3-70b-versatile)
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

## Groq Classifications

Groq adds qualitative context to each company's score:

**academic_signal** — research positioning:
`LEADING` · `CONTRIBUTING` · `FOLLOWING` · `ABSENT`

**wikipedia_signal** — public knowledge activity:
`SURGING` · `ACTIVE` · `QUIET` · `DORMANT`

**combined_insight** — one sentence on what the two signals say together.

**watch_flag** — true when either signal shows an unusual pattern worth monitoring.

---

## Report Structure

Every run produces a markdown report with six sections:

1. **Executive Summary** — companies tracked, dominant count, watch flags, wiki spikes, total papers, total citations
2. **Research Footprint Rankings** — sorted by score; per-company tier, academic signal, wikipedia signal, combined insight, conference presence, edit count, watch flag
3. **Watch Flags** — companies where `watch_flag = true`
4. **Wikipedia Spikes** — companies where `is_spike = true`, with a note that spikes often precede news by 24–72 hours
5. **Conference Presence Matrix** — NeurIPS / ICML / CVPR / ICLR presence per company
6. **Score Breakdown** — scholar (/60) vs Wikipedia (/40) contribution per company

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | n8n (self-hosted) |
| Academic data | Semantic Scholar API — free, no key required |
| Knowledge activity | Wikipedia MediaWiki API — free, no key required |
| LLM | Groq — `llama-3.3-70b-versatile` via HTTP Request nodes |
| Storage | Supabase (PostgreSQL) |
| Output | Markdown report via webhook + archived in Supabase |

---

## Prerequisites

- n8n instance running (self-hosted, v1.x+)
- Supabase project
- Groq API key — [console.groq.com](https://console.groq.com)
- No credentials needed for Semantic Scholar or Wikipedia

---

## Supabase Setup

Run `setup.sql` in the Supabase SQL Editor before the first run. It creates:

- `mindshare_signals` — one row per company per week, unique on `(ticker, run_week)`
- `research_reports` — full markdown report archive per run
- Indexes on `ticker`, `run_week`, `research_footprint_score`, `watch_flag`, `is_spike`

---

## Credentials

Set these as environment variables on the n8n host before starting n8n:

| Variable | Where to get it |
|---|---|
| `GROQ_API_KEY` | console.groq.com → API Keys |
| `PIPELINE_SECRET` | Any random string you choose |

```bash
export GROQ_API_KEY=your-groq-key
export PIPELINE_SECRET=your-secret
npx n8n
```

In the n8n UI, also create:
- A **Supabase** credential and bind it to the two Supabase nodes
- A **Header Auth** credential (`X-Pipeline-Secret` = your `PIPELINE_SECRET`) and bind it to the Manual Pipeline Webhook node

> `SUPABASE_URL` and `SUPABASE_KEY` are handled by the Supabase credential directly — no env vars needed for them.

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
  http://localhost:5678/webhook/run-research-pipeline
```

The full markdown report is returned directly in the response. The Cron trigger runs automatically every Monday at 07:00 UTC once activated.

---

## Known Limitations

- **Semantic Scholar matches on company name in paper metadata** — may include papers not from the company's official research arm.
- **Wikipedia edit count includes bot edits** — not all edits represent human knowledge-building activity.
- **Conference presence depends on the `venue` field** in Semantic Scholar, which is inconsistently populated across papers.
- **First run has no week-over-week comparison** — meaningful trend data starts from the second run.

---

## Project Structure

```
research-footprint-monitor/
├── workflow.json
├── setup.sql
└── README.md
```

---

## Sample Output

```
# Research Footprint Monitor — Signal Report
**Run ID:** b9d4f2a1-7e3c-4b8d-9f2e-3a4b5c6d7e8f
**Generated:** 2026-06-16T07:12:18.440Z
**Week:** 2026-W24

---

## Executive Summary

| Metric | Value |
|---|---|
| Companies tracked | 7 |
| Dominant footprint | 2 |
| Watch flags | 3 |
| Wikipedia spikes | 1 |
| Total papers found | 48 |
| Total citations | 3,241 |

---

## Research Footprint Rankings

### 1. Google (GOOGL) — Score: 88/100
**Tier:** DOMINANT | **Academic signal:** LEADING
| **Wikipedia signal:** ACTIVE
**Research narrative:** Google DeepMind maintains the broadest academic
presence of any watchlist company, with papers at all four top venues
and an average citation count well above the cohort median.
**Combined insight:** Sustained research dominance with steady public
knowledge activity — no spike but consistent deep engagement.
**Conference presence:** NeurIPS, ICML, CVPR, ICLR
**Wikipedia edits (7d):** 8 (5 unique editors)
**Watch flag:** No

### 2. NVIDIA (NVDA) — Score: 76/100
**Tier:** DOMINANT | **Academic signal:** CONTRIBUTING
| **Wikipedia signal:** SURGING
**Research narrative:** NVIDIA's academic output has intensified around
inference optimization and world models, with NeurIPS and CVPR presence.
Wikipedia edit activity spiked this week — 18 edits across 9 editors.
**Combined insight:** A Wikipedia spike alongside accelerating GitHub
activity and strong conference presence suggests a coordinated build-up
ahead of a potential announcement.
**Conference presence:** NeurIPS, CVPR
**Wikipedia edits (7d):** 18 (9 unique editors)
**Watch flag:** ⚠ YES

### 3. Microsoft (MSFT) — Score: 61/100
**Tier:** STRONG | **Academic signal:** CONTRIBUTING
| **Wikipedia signal:** ACTIVE
**Research narrative:** Microsoft Research output is concentrated in
applied ML and infrastructure papers, with ICML presence but limited
NeurIPS footprint compared to peers.
**Combined insight:** Solid but not dominant research presence; public
knowledge activity is normal with no unusual signals.
**Conference presence:** ICML
**Wikipedia edits (7d):** 6 (4 unique editors)
**Watch flag:** No

---

## Watch Flags

- ⚠ **NVIDIA (NVDA)** — Wikipedia spike (18 edits) coincides with
  GitHub acceleration. Combined insight: pre-announcement build-up.
- ⚠ **Meta (META)** — Academic signal shifted from FOLLOWING to
  CONTRIBUTING this week. LLaMA-related papers at ICML.
- ⚠ **Intel (INTC)** — ABSENT at all four top conferences for the
  second consecutive week while GitHub velocity is DECELERATING.

---

## Wikipedia Spikes
*> 10 edits/week — often precede news cycles by 24–72 hours*

| Company | Ticker | Edits (7d) | Unique Editors | Last Edit |
|---|---|---|---|---|
| NVIDIA | NVDA | 18 | 9 | 2026-06-15T22:41:00Z |

---

## Conference Presence Matrix

| Company | NeurIPS | ICML | CVPR | ICLR | Papers | Citations |
|---|---|---|---|---|---|---|
| Google | ✓ | ✓ | ✓ | ✓ | 14 | 1,842 |
| NVIDIA | ✓ | ✗ | ✓ | ✗ | 9 | 734 |
| Microsoft | ✗ | ✓ | ✗ | ✗ | 7 | 412 |
| Meta | ✗ | ✓ | ✗ | ✗ | 8 | 156 |
| AMD | ✗ | ✗ | ✗ | ✗ | 2 | 61 |
| Apple | ✗ | ✗ | ✗ | ✗ | 4 | 28 |
| Intel | ✗ | ✗ | ✗ | ✗ | 4 | 8 |

---

## Score Breakdown

| Company | Scholar (/60) | Wikipedia (/40) | Total (/100) | Tier |
|---|---|---|---|---|
| Google | 60 | 28 | 88 | DOMINANT |
| NVIDIA | 48 | 28 | 76 | DOMINANT |
| Microsoft | 33 | 28 | 61 | STRONG |
| Meta | 33 | 28 | 61 | STRONG |
| AMD | 10 | 20 | 30 | PRESENT |
| Apple | 10 | 20 | 30 | PRESENT |
| Intel | 10 | 10 | 20 | MINIMAL |
```

---

## Author

**Sahiti Nallamolu**

- LinkedIn: [linkedin.com/in/sahitinallamolu](https://www.linkedin.com/in/sahitinallamolu/)
- Humanitarians AI Fellow

---

*Stack: n8n + Semantic Scholar API + Wikipedia MediaWiki API + Groq (llama-3.3-70b-versatile) + Supabase*

---