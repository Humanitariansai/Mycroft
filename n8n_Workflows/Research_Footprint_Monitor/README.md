# Research Footprint Monitor — Mycroft Agent 5

The Research Footprint Monitor measures how much of the AI field's attention each watchlist company "occupies," combining two signals that operate on **very different time horizons**. Academic output from Semantic Scholar reflects *research dominance* — where a company invests in the science that will ship in 6–12 months — while Wikipedia edit velocity reflects *public knowledge activity* — the days-scale churn that precedes news cycles by 24–72 hours. Fused into a single `mindshare_score` (0–100) per company per week, the two horizons together reveal whether a company's mindshare is being built quietly in labs or surging visibly in the public record — and where the two diverge.

---

## Mycroft Architecture

| Agent | Name | Signal | Output table |
|---|---|---|---|
| 1 | Reddit Anxiety Index | Retail sentiment / fear | `anxiety_runs` |
| 2 | Patent Velocity Tracker | IP filing cadence | `patent_runs` |
| 3 | Media Narrative Tracker | Press narrative framing | `media_narratives_raw` |
| 4 | GitHub Commit Velocity | Open-source dev activity | `github_signals` |
| 5 | **Research Footprint Monitor** | **Academic + public knowledge mindshare** | **`mindshare_signals`, `research_reports`** |
| 6 | Mindshare Gap / Pattern | Cross-signal asymmetry detection | *(reads `mindshare_signals`)* |

---

## The Two Signals

### Layer A — Semantic Scholar (research lag: 6–12 months)
Queries the [Semantic Scholar Graph API](https://api.semanticscholar.org/) for recent papers (`year=2023-`) whose metadata matches each company. We measure:
- **Paper count** — raw academic output volume.
- **Conference presence** — papers at the top-tier AI venues **NeurIPS, ICML, CVPR, ICLR**. Presence at these venues is the strongest available proxy for *frontier* research investment, not just publishing volume — it signals a company is competing at the field's leading edge.
- **Citations** — `total` and `avg`, a rough quality/impact signal.

Academic output is a **lagging** indicator: a paper at NeurIPS today reflects a research bet made 6–12 months ago and points to products 6–12 months out.

### Layer B — Wikipedia (knowledge lag: days)
Queries the [Wikipedia MediaWiki API](https://www.mediawiki.org/wiki/API:Revisions) for revisions to each company's page over the **last 7 days**. We measure:
- **Edit count (7d)** and **edit velocity** (edits/day).
- **Unique editors** — breadth of attention vs. a single active editor.
- **Spike flag** — `> 10 edits/week`.

Edit velocity is a **leading** indicator: Wikipedia edit spikes typically **precede mainstream news cycles by 24–72 hours** as editors react to events before coverage peaks.

---

## Footprint Score Breakdown (0–100)

`research_footprint_score = min(100, scholar_component + wikipedia_component)`

### Scholar component (0–60)
| Rule | Points |
|---|---|
| `paper_count >= 8` | 30 |
| `paper_count >= 4` | 20 |
| `paper_count >= 1` | 10 |
| has NeurIPS | +8 |
| has ICML | +7 |
| has CVPR | +5 |
| has ICLR | +5 |
| `avg_citations > 50` | +5 |

### Wikipedia component (0–40)
| Rule | Points |
|---|---|
| `edit_count_7d >= 20` | 20 |
| `edit_count_7d >= 10` | 15 |
| `edit_count_7d >= 5` | 10 |
| else (baseline) | 5 |
| `unique_editors >= 10` | +10 |
| `unique_editors >= 5` | +5 |
| `is_spike` | +10 |

### Tiers
| Score | Tier |
|---|---|
| ≥ 75 | **DOMINANT** |
| ≥ 50 | **STRONG** |
| ≥ 25 | **PRESENT** |
| < 25 | **MINIMAL** |

---

## Tech Stack

| Component | Role | Credential? |
|---|---|---|
| **n8n** | Workflow orchestration | self-hosted / cloud |
| **Semantic Scholar API** | Layer A — academic papers | **FREE — no key, no auth** (100 req / 5 min) |
| **Wikipedia MediaWiki API** | Layer B — page revisions | **FREE — no key, no auth** |
| **Groq** (`llama-3.3-70b-versatile`) | Footprint narrative analysis | API key |
| **Supabase** (PostgreSQL) | Signal + report storage | URL + key |

---

## Prerequisites
- A running **n8n** instance (self-hosted or cloud).
- A **Supabase** project.
- A **Groq** API key ([console.groq.com](https://console.groq.com)).
- `curl` (for manual triggering).

---

## Supabase Setup
1. Open your Supabase project → **SQL Editor**.
2. Paste and run the contents of [setup.sql](setup.sql).
3. This creates `mindshare_signals` and `research_reports`, all indexes, and disables RLS for service-key writes.

---

## Credentials

| Credential | n8n env var | Where to get |
|------------------|------------------|-----------------------|
| Supabase URL | `SUPABASE_URL` | Supabase project settings |
| Supabase key | `SUPABASE_KEY` | Supabase API settings |
| Groq API key | `GROQ_API_KEY` | console.groq.com |
| Pipeline secret | `PIPELINE_SECRET` | Any random string |

> **Note:** The Semantic Scholar and Wikipedia APIs require **no credentials** — no key, no token, no auth header.

Configure in n8n:
- **Supabase** node credential → use `SUPABASE_URL` + `SUPABASE_KEY`.
- The **Manual Pipeline Webhook** uses Header Auth (`X-Pipeline-Secret`) — set its value to `PIPELINE_SECRET`.
- The **Groq** node reads `Authorization: Bearer {{ $env.GROQ_API_KEY }}`.

---

## n8n Import
1. n8n → **Workflows** → **Import from File**.
2. Select [workflow.json](workflow.json).
3. Open the two **Supabase** nodes and bind your Supabase credential.
4. Open the **Manual Pipeline Webhook** and bind/confirm the Header Auth credential.
5. Ensure `GROQ_API_KEY` and `PIPELINE_SECRET` exist as environment variables on the n8n host.

---

## First Run

The pipeline runs automatically every **Monday 07:00 UTC** via the Cron trigger. To trigger manually:

```bash
curl -H "X-Pipeline-Secret: your-secret" \
  http://localhost:5678/webhook/run-research-pipeline
```

The response body is the full markdown report (`Content-Type: text/markdown`). A copy is archived in `research_reports`, and per-company rows are upserted into `mindshare_signals` (conflict key `ticker,run_week`).

---

## Reading the Report

- **Tier** (`DOMINANT` / `STRONG` / `PRESENT` / `MINIMAL`) — overall footprint strength from the combined score.
- **Academic signal** (`LEADING` / `CONTRIBUTING` / `FOLLOWING` / `ABSENT`) — Groq's read of research positioning.
- **Wikipedia signal** (`SURGING` / `ACTIVE` / `QUIET` / `DORMANT`) — Groq's read of public knowledge activity.
- **Watch flag** — either signal shows an unusual pattern worth monitoring.
- **Conference Presence Matrix** — which top venues each company appears in.
- **Score Breakdown** — scholar (/60) vs. Wikipedia (/40) contribution.
- **Wikipedia Spikes** — `>10 edits/week`; these often *lead* news by 24–72 hrs.

The most actionable rows are **divergences**: high academic / low public (quiet research bet) or low academic / surging public (event-driven attention without underlying research depth).

---

## How Output Connects to Agent 6

Agent 6 (the **Mindshare Gap / Pattern** agent) reads `mindshare_signals` and cross-references the other agents:

- A **Wikipedia spike** (`is_spike = true`) combined with **no corresponding Reddit activity** (Agent 1's `anxiety_runs`) is flagged as an **`INFORMATION_ASYMMETRY_WINDOW`** — public-record attention is moving before retail sentiment has caught up, the leading edge of a potential news cycle.
- Sustained academic dominance with flat public knowledge activity signals durable, under-the-radar research strength.

---

## Project Structure

```
research-footprint-monitor/
├── workflow.json
├── setup.sql
└── README.md
```

---

*Mycroft — Research Footprint Monitor | Agent 5*
*Stack: n8n + Semantic Scholar API + Wikipedia MediaWiki API + Groq (llama-3.3-70b) + Supabase*
