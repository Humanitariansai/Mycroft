# Hacker News AI Buzz Tracker

> **Developed by:** Om Mali (mali.om@northeastern.edu)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=flat&logo=github&logoColor=white)](https://github.com/Humanitariansai)

Part of the **Mycroft** project — *"Using AI to Invest in AI."*

## What Is This

The Hacker News AI Buzz Tracker is an n8n agent that turns developer discussion on Hacker News
into a quantified, comparable **developer-attention signal** for the AI sector. It watches a
watchlist of AI companies and products, scores how much attention each is getting over a trailing
window, and reports the daily movers.

The thesis: mindshare leads price in the AI sector, and the technical community is where mindshare
forms first. AI launches, model releases, outages, and controversies get debated on Hacker News
before they reach mainstream financial coverage. This agent makes that early, scattered attention
visible as a clean number. **It measures attention, not direction** — it is one disciplined input
among many, not a trade trigger.

## Signals

| Signal | Source | Description |
|--------|--------|-------------|
| **Buzz Score** | Code node | Overall HN attention per entity, 0–100 (deterministic). |
| **Buzz Velocity** | Code node | Change versus the entity's trailing average / previous run. |
| **Front Page Breakouts** | Code node | Count of stories crossing a high points threshold. |
| **Narrative Theme** | LLM (Month 2) | launch, outage, funding, research, controversy, or hiring. |
| **Reception Tone** | LLM (Month 2) | bullish, bearish, or neutral developer reception. |

See `design.md` for the full Buzz Score formula and data model.

## Architecture

```
Schedule Trigger (daily, configurable)
  → Set: Watchlist (entity, query terms, ticker, thresholds)
  → Split In Batches (loop entities)
      → HTTP Request: HN Algolia search_by_date (trailing window filter)
  → Code: aggregate per-entity metrics + compute Buzz Score (0–100)
  → Postgres (Supabase): read previous snapshot
  → Code: compute Buzz Velocity vs. previous run
  → LLM node (Groq Llama 3.1 or Claude): narrative, theme, reception tone
  → Code: merge into ranked leaderboard
  → Postgres (Supabase): insert run snapshot
  → IF: any entity crosses an alert threshold
      → Send Email: HTML digest (top movers, scores, narratives)
  → (optional) Webhook: GET /webhook/dashboard serves HTML
```

## Prerequisites

- **n8n** running locally (Docker recommended):
  ```bash
  docker volume create n8n_data
  docker run -it --rm --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n
  ```
  Then open http://localhost:5678.
- **Supabase** free-tier project (Postgres) for snapshots — *added Week 4*.
- A free **Groq API key** (or an Anthropic/Claude key) for the LLM narrative layer — *added Week 5*.
- No key is needed for the Hacker News Algolia data source.

## Setup

> _TODO (filled in Weeks 4–5 as the workflow is built):_
1. Copy `.env.example` to `.env` and fill in your keys (kept out of git).
2. Import `workflow.json` into n8n (**Workflows → Import from File**).
3. Configure credentials: Postgres (Supabase) and SMTP (email).
4. Edit the **Watchlist** Set node (or `watchlist.json`) to set your entities and thresholds.
5. Activate the workflow and run a manual execution to verify.

## Schema

Snapshots are stored in Supabase Postgres in the `hn_buzz_runs` table.

> _TODO: `DATABASE_SETUP.md` with the full schema is a Week 4 deliverable._

```sql
create table hn_buzz_runs (
  id uuid default gen_random_uuid() primary key,
  created_at timestamptz default now(),
  run_date text,
  window_hours int,
  leaderboard jsonb,   -- ranked entities: score, velocity, top story
  narratives jsonb,    -- per-entity narrative, theme, tone (Month 2)
  raw_metrics jsonb    -- volume, points, comments, front-page counts
);
```

## License

MIT License — see repository for full license text.

## Support

- **Email:** mali.om@northeastern.edu
- **GitHub Issues:** [Mycroft Repository Issues](https://github.com/Humanitariansai/Mycroft/issues)
