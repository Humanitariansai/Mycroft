# Media Narrative Tracker — Mycroft Agent 3

## 1. What it does

The Media Narrative Tracker monitors five financial-news RSS feeds and uses Claude to score each article for **information age** — how genuinely new the underlying claim is versus a recycled narrative being retold. It tells an investor when a story carries fresh signal and when it is merely echo, surfacing the result through a Supabase-backed dashboard.

## 2. Where it fits in Mycroft

Mycroft is an AI-powered investment-intelligence framework focused on the AI sector. The Media Narrative Tracker sits one layer above the data-collection agents, judging the *quality* of incoming media rather than the data itself.

| # | Agent | Output table | Status |
|---|-------|--------------|--------|
| 1 | Reddit Anxiety Index | `anxiety_runs` | ✅ Built |
| 2 | Patent Velocity Tracker | `patent_runs` | ✅ Built |
| 3 | **Media Narrative Tracker** | `media_narratives_raw` | ✅ **Built (this agent)** |
| 4 | Story Consistency | `story_consistency` | ⬜ Not built |
| 5 | Four-Layer Blindspot Detector | (consumes 1–4) | ⬜ Not built |

## 3. The three Claude signals

Three Claude LLM Chain nodes run in parallel against the same batch of new articles:

| Node | Signal | Output fields |
|------|--------|---------------|
| Claude 1 — Core Claim Extractor | The single factual claim, stripped of editorial framing | `core_claim`, `claim_type` |
| Claude 2 — Information Age Scorer | Freshness of the underlying claim (0–100) | `information_age_score`, `is_recycled`, `narrative_label` |
| Claude 3 — Company Mention Extractor | Watchlist companies referenced (alias-aware) | `companies_mentioned` |

The **Signal Assembler** merges all three by `article_url` into one record per article.

## 4. Tech stack

| Layer | Technology |
|-------|-----------|
| Orchestration | n8n (self-hosted, workflow.json) |
| LLM | Anthropic Claude (LLM Chain nodes) |
| Storage | Supabase (PostgreSQL + jsonb) |
| Ingestion | 5 RSS feeds via HTTP Request nodes |
| Dashboard | Inline single-page HTML served by n8n |

## 5. Prerequisites

- A running n8n instance (self-hosted, v1.x) — local default `http://localhost:5678`
- A Supabase project
- An Anthropic API key
- Node.js only insofar as n8n requires it (no extra libraries — the XML parser is pure regex)

## 6. Supabase setup

Run [setup.sql](setup.sql) in the Supabase SQL editor. It creates:

- `media_narratives_raw` — primary signal table, with `article_url` **unique** (the deduplication key)
- `agent_runs` — pipeline run history
- six indexes (incl. a **GIN** index on `companies_mentioned`)
- the `novel_signals` view (score ≥ 60, last 48h)

```sql
-- key constraint that powers dedup + upsert:
article_url text unique not null
```

## 7. Credential placeholders

| Credential | n8n name | Where to get it |
|------------|----------|-----------------|
| Supabase URL | `SUPABASE_URL` | Supabase project settings |
| Supabase anon key | `SUPABASE_KEY` | Supabase API settings |
| Anthropic API key | `ANTHROPIC_KEY` | console.anthropic.com |
| Pipeline secret | `PIPELINE_SECRET` | Generate any string |

Set `SUPABASE_URL`, `SUPABASE_KEY`, and `PIPELINE_SECRET` as **environment variables** on the n8n host (the Code nodes read `$env.*`). Configure the Anthropic, Supabase, and Header-Auth credentials in **n8n → Credentials**. The Manual Pipeline Webhook uses Header Auth with header `X-Pipeline-Secret` matching `PIPELINE_SECRET`.

## 8. n8n import steps

1. n8n → **Workflows → Import from File** → select [workflow.json](workflow.json).
2. Open each of the three **Anthropic Model** sub-nodes and select your Anthropic credential.
3. Open **Insert to Supabase** and **Fetch Dashboard Data** and select your Supabase credential.
4. Open **Manual Pipeline Webhook** and select the Header-Auth credential (`X-Pipeline-Secret`).
5. Ensure `SUPABASE_URL`, `SUPABASE_KEY`, `PIPELINE_SECRET` exist in the host environment.
6. Save. (The workflow ships `active: false` — activate it to enable the 6-hour Cron.)

## 9. First run

- **Manual trigger:**
  ```bash
  curl -H "X-Pipeline-Secret: <your PIPELINE_SECRET>" \
    "http://localhost:5678/webhook/run-media-pipeline"
  ```
- Or click **Execute Workflow** in the editor.
- On first run, every article is new (the table is empty) so all are scored and inserted. Subsequent runs deduplicate against the last 7 days.
- Open the dashboard URL in a browser to view results.

## 10. Webhook URLs

```
Pipeline:  http://localhost:5678/webhook/run-media-pipeline
Dashboard: http://localhost:5678/webhook/media-narrative-dashboard
```

## 11. Known limitations

1. **RSS feed coverage is not neutral.** The five sources (Financial Times, Reuters, Seeking Alpha, CNBC, Yahoo Finance) each carry editorial biases. Trade-press or niche narratives won't be detected until they surface in these five sources, so the agent's view of "what the media is saying" is structurally skewed toward mainstream financial outlets.
2. **Information-age scoring depends on Claude consistency.** Whether Claude assigns the same recycled narrative a comparable score across separate runs is unvalidated; scoring drift over time is possible.
3. **No ground truth for "recycled" classification.** No labeled dataset exists to validate what the agent calls recycled vs. novel — the `is_recycled` flag and age score are model judgments, not measured facts.
4. **Narrative-label stability.** Claude may phrase the same underlying narrative slightly differently across runs (e.g. "AI chip export curbs" vs. "AI chip export restrictions"), which prevents clean grouping of a narrative over time in the clusters view.

## 12. How this connects to Agent 5 (Four-Layer Blindspot Detector)

Agent 5 consumes the outputs of Agents 1–4 to detect investor blindspots. The Media Narrative Tracker feeds two of its patterns directly:

- **Pattern 1 — `NARRATIVE_RECYCLING_TRAP`:** uses `is_recycled` and `narrative_label` to flag when an investor is reacting to recycled coverage (low `information_age_score`) as though it were new information — i.e. mistaking echo for signal.
- **Pattern 4 — `INFORMATION_ASYMMETRY_WINDOW`:** uses high `information_age_score` (genuinely novel) signals, cross-referenced against company mentions and the anxiety/patent agents, to identify short windows where new information has appeared but is not yet broadly priced in.

## 13. Project structure

```
media-narrative-tracker/
├── workflow.json
├── setup.sql
└── README.md
```
