# Media Narrative Tracker — Mycroft Agent 3

## 1. What it does

The Media Narrative Tracker monitors five financial-news RSS feeds and uses the Groq API (`llama-3.3-70b-versatile`) to score each article for **information age** — how genuinely new the underlying claim is versus a recycled narrative being retold. It produces a structured markdown **signal report** that is returned directly in the webhook response and stored in Supabase, telling an investor when a story carries fresh signal and when it is merely echo.

## 2. Mycroft architecture

| # | Agent | Output table(s) | Status |
|---|-------|-----------------|--------|
| 1 | Reddit Anxiety Index | `anxiety_runs` | ✅ Built |
| 2 | Patent Velocity Tracker | `patent_runs` | ✅ Built |
| 3 | **Media Narrative Tracker** | `media_narratives_raw`, `narrative_reports` | ✅ **Built (this agent)** |
| 4 | Story Consistency | `story_consistency` | ⬜ Not built |
| 5 | Four-Layer Blindspot Detector | `blindspot_reports` | ⬜ Not built |

## 3. The three Groq signals

Three parallel HTTP Request nodes call the Groq API against the same batch of new articles:

| Node | Signal | Output fields |
|------|--------|---------------|
| Groq 1 — Core Claim Extractor | The single factual claim, stripped of editorial framing | `core_claim`, `claim_type` |
| Groq 2 — Information Age Scorer | Freshness of the underlying claim (0–100) | `information_age_score`, `is_recycled`, `narrative_label` |
| Groq 3 — Company Mention Extractor | Watchlist companies referenced (alias-aware) | `companies_mentioned` |

The **Signal Assembler** merges all three by `article_url` into one record per article.

## 4. Report structure

The Generate Report node produces a markdown report with these sections:

1. **Executive Summary** — counts, companies, most active narrative
2. **Novel Signals** — articles with score ≥ 60 (worth reading)
3. **Recycled Narratives** — articles with score < 40 (noise)
4. **Narrative Clusters** — articles grouped by narrative label
5. **Company Coverage** — watchlist companies appearing this run
6. **Signal Classification Summary** — counts per score band

(Plus a Known Limitations note and footer.)

## 5. Tech stack

| Layer | Technology |
|-------|-----------|
| Orchestration | n8n (self-hosted, workflow.json) |
| LLM | Groq API — `llama-3.3-70b-versatile` (via HTTP Request nodes) |
| Storage | Supabase (PostgreSQL + jsonb) |
| Ingestion | 5 RSS feeds (FT, Reuters, Seeking Alpha, CNBC, Yahoo Finance) |
| Output | Markdown report (webhook response + `narrative_reports`) |

## 6. Prerequisites

- A running n8n instance (self-hosted, v1.x) — local default `http://localhost:5678`
- A Supabase project
- A Groq API key
- No external libraries — the XML parser is pure regex

## 7. Supabase setup

Run [setup.sql](setup.sql) in the Supabase SQL editor. It creates:

- `media_narratives_raw` — primary signal table, `article_url` **unique** (the deduplication key)
- `narrative_reports` — full markdown report per run
- six indexes (incl. a **GIN** index on `companies_mentioned`)
- the `novel_signals` view (score ≥ 60, last 48h)

```sql
-- key constraint that powers dedup + upsert:
article_url text unique not null
```

## 8. Credentials

| Credential | n8n env var | Where to get |
|------------|-------------|--------------|
| Supabase URL | `SUPABASE_URL` | Supabase project settings |
| Supabase key | `SUPABASE_KEY` | Supabase API settings |
| Groq API key | `GROQ_API_KEY` | console.groq.com |
| Pipeline secret | `PIPELINE_SECRET` | Any random string |

Set these as **environment variables** on the n8n host (the Code and HTTP nodes read `$env.*`). Also configure the Supabase credential in **n8n → Credentials** for the two Supabase nodes, and the Header-Auth credential (header `X-Pipeline-Secret` = `PIPELINE_SECRET`) for the Manual Pipeline Webhook.

## 9. n8n import steps

1. n8n → **Workflows → Import from File** → select [workflow.json](workflow.json).
2. Open **Insert to Supabase** and **Store Report in Supabase** and select your Supabase credential.
3. Open **Manual Pipeline Webhook** and select the Header-Auth credential (`X-Pipeline-Secret`).
4. Ensure `SUPABASE_URL`, `SUPABASE_KEY`, `GROQ_API_KEY`, `PIPELINE_SECRET` exist in the host environment.
5. Save. (Ships `active: false` — activate it to enable the 6-hour Cron.)

## 10. First run

```bash
curl -H "X-Pipeline-Secret: your-secret" \
  http://localhost:5678/webhook/run-media-pipeline
```

The full markdown report is returned directly in the response (`Content-Type: text/markdown`). On the first run, every article is new (empty table) so all are scored and inserted; later runs deduplicate against the last 7 days.

## 11. Reading the report

Each article carries an **information age score**:

| Score | Label | Meaning |
|-------|-------|---------|
| 80–100 | Genuinely New | First time this specific claim appears — new data, new event |
| 50–79 | Partially New | New development in an ongoing story |
| 20–49 | Likely Recycled | Same claim seen before, new framing |
| 0–19 | Recycled | Commentary / restatement of weeks-old news |

`is_recycled` is `true` when the score is below 40. Prioritize the **Novel Signals** section; treat the **Recycled Narratives** table as noise.

## 12. Known limitations

1. **RSS coverage limited to 5 outlets** (FT, Reuters, Seeking Alpha, CNBC, Yahoo Finance). Trade-press and niche narratives are missed until picked up by these sources, so the agent's view of "the media" is structurally skewed toward mainstream financial outlets.
2. **Information age scores are Groq estimates** with no labeled ground-truth validation — `is_recycled` and the score are model judgments, not measured facts.
3. **Narrative label consistency across runs is unvalidated.** Groq may phrase the same underlying narrative slightly differently between runs, which prevents clean grouping of a narrative over time.
4. **Groq model output format may vary.** The Signal Assembler strips ```json fences and wraps each `JSON.parse()` in try/catch with a null fallback, but malformed-output edge cases can still drop a field for an article.

## 13. How output connects to Agent 5 (Four-Layer Blindspot Detector)

Agent 5 reads from the `novel_signals` view and the `media_narratives_raw` table to power two of its patterns:

- **Pattern 1 — `NARRATIVE_RECYCLING_TRAP`:** uses `is_recycled` and `narrative_label` to flag when an investor is reacting to recycled coverage (low `information_age_score`) as though it were new — mistaking echo for signal.
- **Pattern 4 — `INFORMATION_ASYMMETRY_WINDOW`:** uses high-score novel signals from `novel_signals`, cross-referenced with company mentions and the anxiety/patent agents, to identify short windows where new information has appeared but is not yet broadly priced in.

## 14. Project structure

```
media-narrative-tracker/
├── workflow.json
├── setup.sql
└── README.md
```
