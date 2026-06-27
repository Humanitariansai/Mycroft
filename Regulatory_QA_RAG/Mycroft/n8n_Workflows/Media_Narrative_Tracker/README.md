# Media Narrative Tracker

Most financial news isn't new. It's the same underlying claim retold by different outlets over different days, creating the illusion of signal where there is only echo. Reuters publishes something, CNBC picks it up, Yahoo Finance recaps it, Seeking Alpha frames it as analysis — four articles, one piece of information. By the time retail investors react, the information is days old.

The Media Narrative Tracker measures this directly. Every six hours it pulls articles from five financial RSS feeds, extracts the core claim from each article, and scores it for **information age** — a number from 0 to 100 representing how genuinely new the underlying claim is. Articles scoring above 60 carry fresh signal worth reading. Articles scoring below 40 are recycled narrative dressed in today's language. The output is a structured markdown report that tells you exactly when to pay attention and when to ignore the noise.

---

## How It Works

Three parallel Groq calls run against the same batch of new articles, each doing a different job:

**Core Claim Extractor** strips editorial framing and pulls the single factual claim an article is making, along with its claim type: earnings, product, partnership, regulatory, personnel, market move, macro, or other.

**Information Age Scorer** asks how fresh that claim actually is. The scoring guide:

| Score | Label | Meaning |
|---|---|---|
| 80–100 | Genuinely New | First time this specific claim appears |
| 50–79 | Partially New | New development in an ongoing story |
| 20–49 | Likely Recycled | Same claim, new framing |
| 0–19 | Recycled | Commentary or restatement of old news |

**Company Mention Extractor** identifies which watchlist companies appear in the article using alias matching — "Jensen Huang" routes to NVIDIA, "Lisa Su" to AMD — so informal references aren't missed.

The Signal Assembler merges all three outputs by article URL into one record per article, upserts to Supabase, and generates the report.

---

## Architecture

```
Cron Trigger (every 6 hours)
  +
Manual Webhook  GET /run-media-pipeline
  ↓
5 parallel RSS fetches
  Financial Times · Reuters · Seeking Alpha · CNBC · Yahoo Finance
  ↓
Merge RSS Results  (mergeByPosition, 5 inputs)
  ↓
Parse & Clean Articles  (regex XML parser, no external libraries)
  ↓
Deduplicate Against Supabase  (skips articles seen in last 7 days)
  ↓
Aggregate for Groq
  ↓
3 parallel Groq calls  (llama-3.3-70b-versatile)
  Groq 1: Core Claim Extractor
  Groq 2: Information Age Scorer
  Groq 3: Company Mention Extractor
  ↓
Merge Groq Outputs  (waitForAll, 3 inputs)
  ↓
Signal Assembler
  ↓
Insert to Supabase  (upsert on article_url)
  ↓
Generate Report
  ↓
Store Report in Supabase
  ↓
Pipeline Response  (returns markdown report, Content-Type: text/markdown)
```

---

## Report Structure

Every run produces a markdown report with six sections:

1. **Executive Summary** — articles processed, novel count, recycled count, companies mentioned, most active narrative
2. **Novel Signals** — articles scoring ≥ 60, each with headline, source, score, core claim, narrative label, and URL
3. **Recycled Narratives** — articles scoring < 40 in a compact table
4. **Narrative Clusters** — articles grouped by narrative label with average age score per cluster
5. **Company Coverage** — watchlist companies appearing this run with mention count and average score
6. **Signal Classification Summary** — counts per score band (80–100, 50–79, 20–49, 0–19)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | n8n (self-hosted) |
| LLM | Groq — `llama-3.3-70b-versatile` via HTTP Request nodes |
| Storage | Supabase (PostgreSQL + jsonb) |
| Ingestion | 5 RSS feeds |
| Output | Markdown report via webhook + archived in Supabase |

---

## Prerequisites

- n8n instance running (self-hosted, v1.x+)
- Supabase project
- Groq API key — [console.groq.com](https://console.groq.com)

---

## Supabase Setup

Run `setup.sql` in the Supabase SQL Editor before the first run. It creates:

- `media_narratives_raw` — primary signal table with `article_url unique` as the deduplication key
- `narrative_reports` — full markdown report archive per run
- Six indexes including a GIN index on `companies_mentioned`
- `novel_signals` view — articles scoring ≥ 60 from the last 48 hours

---

## Credentials

Set these as environment variables on the n8n host before starting n8n:

| Variable | Where to get it |
|---|---|
| `SUPABASE_URL` | Supabase → Project Settings → API |
| `SUPABASE_KEY` | Supabase → Project Settings → API (anon key) |
| `GROQ_API_KEY` | console.groq.com → API Keys |
| `PIPELINE_SECRET` | Any random string you choose |

```bash
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_KEY=your-anon-key
export GROQ_API_KEY=your-groq-key
export PIPELINE_SECRET=your-secret
npx n8n
```

In the n8n UI, also create:
- A **Supabase** credential and bind it to the two Supabase nodes
- A **Header Auth** credential (`X-Pipeline-Secret` = your `PIPELINE_SECRET`) and bind it to the Manual Pipeline Webhook node

---

## Import & Activate

1. n8n → **Workflows → Import from File** → select `workflow.json`
2. Open **Insert to Supabase** → bind your Supabase credential
3. Open **Store Report in Supabase** → bind your Supabase credential
4. Open **Manual Pipeline Webhook** → bind your Header Auth credential
5. Save — leave inactive until you've done a manual test run

---

## First Run

```bash
curl -H "X-Pipeline-Secret: your-secret" \
  http://localhost:5678/webhook/run-media-pipeline
```

The full markdown report is returned directly in the response. On the first run every article is new (empty table) so all are scored and inserted. Subsequent runs deduplicate against the last 7 days — typically 60–80% of articles are skipped as already seen.

The Cron trigger runs automatically every 6 hours once the workflow is activated.

---

## Known Limitations

1. **RSS coverage is limited to 5 mainstream outlets.** Trade press and niche financial newsletters are not monitored — narratives breaking there won't appear until picked up by these sources.
2. **Information age scores are model estimates.** There is no labeled ground truth dataset validating what Groq calls recycled vs. novel.
3. **Narrative label consistency is unvalidated.** Groq may phrase the same underlying story differently across runs, which breaks clean grouping in the Narrative Clusters section over time.
4. **Groq output format may vary.** The Signal Assembler strips JSON fences and wraps each parse in try/catch with a null fallback, but malformed responses can still drop a field for an article.

---

## Project Structure

```
media-narrative-tracker/
├── workflow.json
├── setup.sql
└── README.md
```

---


## Sample Output

```
# Media Narrative Tracker — Signal Report
**Run ID:** 3f8a1c2d-e4b5-4f6a-9c8d-1e2f3a4b5c6d
**Generated:** 2026-06-16T06:14:32.881Z
**Period:** Last 6 hours

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Articles processed | 34 |
| Novel signals (score ≥ 60) | 5 |
| Recycled narratives | 21 |
| Companies mentioned | NVIDIA, Microsoft, Google, Meta |
| Most active narrative | AI chip export restrictions |

---

## Novel Signals
*Articles with information age score ≥ 60 — worth reading*

### Commerce Department Issues New AI Chip Export Rules
**Source:** Reuters | **Score:** 91/100 | **Claim type:** regulatory
| **Companies:** NVDA, INTC
**Core claim:** The Commerce Department issued updated export control rules
restricting shipments of advanced AI chips to 12 additional countries
effective immediately.
**Narrative:** AI chip export restrictions
**Published:** 2026-06-16T04:22:00.000Z
**URL:** https://reuters.com/...

### Microsoft Announces Azure AI Foundry General Availability
**Source:** Financial Times | **Score:** 84/100 | **Claim type:** product
| **Companies:** MSFT
**Core claim:** Microsoft confirmed Azure AI Foundry reached general
availability, offering enterprise customers managed model fine-tuning
at scale.
**Narrative:** Microsoft enterprise AI expansion
**Published:** 2026-06-16T03:10:00.000Z
**URL:** https://ft.com/...

---

## Recycled Narratives

| Headline | Source | Score | Narrative Label |
|---|---|---|---|
| Fed Officials Signal Patience on Rate Cuts | CNBC | 18 | Fed rate cut expectations |
| NVIDIA Data Center Revenue Growth Continues | Seeking Alpha | 24 | NVIDIA data center growth |
| AI Spending Remains Strong Despite Macro Concerns | Yahoo Finance | 31 | AI infrastructure spending |

---

## Narrative Clusters

**AI chip export restrictions** — 4 articles, avg score: 67
Sources: Reuters, Financial Times, CNBC, Yahoo Finance

**Fed rate cut expectations** — 8 articles, avg score: 19
Sources: CNBC, Yahoo Finance, Seeking Alpha, Reuters

**NVIDIA data center growth** — 6 articles, avg score: 28
Sources: Seeking Alpha, Yahoo Finance, CNBC

---

## Company Coverage

| Company | Ticker | Mentions | Avg Age Score |
|---|---|---|---|
| NVIDIA | NVDA | 11 | 34 |
| Microsoft | MSFT | 6 | 71 |
| Google | GOOGL | 4 | 48 |
| Meta | META | 3 | 29 |

---

## Signal Classification Summary

| Score Range | Label | Count |
|---|---|---|
| 80–100 | Genuinely New | 3 |
| 50–79 | Partially New | 2 |
| 20–49 | Likely Recycled | 14 |
| 0–19 | Recycled | 15 |
```

---

## Author

**Sahiti Nallamolu**

- LinkedIn: [linkedin.com/in/sahitinallamolu](https://www.linkedin.com/in/sahitinallamolu/)
- Humanitarians AI Fellow

---

*Stack: n8n + Groq (llama-3.3-70b-versatile) + Supabase*

---