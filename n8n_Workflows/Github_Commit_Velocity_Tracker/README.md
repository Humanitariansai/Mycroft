# GitHub Commit Velocity Tracker — Mycroft Agent 4

Tracks **weekly engineering activity** across 7 AI watchlist companies using the
free **GitHub REST API**, detects week-over-week commit velocity acceleration
before product announcements, persists signals to **Supabase**, and returns a
structured markdown report over a webhook.

No dashboard. **Report only.**

---

## 1. What This Agent Does

Engineering velocity is a **leading indicator**. The pace at which a company's
public repositories are pushed, starred, and expanded tends to move *before* the
press release — a sustained acceleration in active repos often precedes a product
launch, an SDK release, or a research milestone by weeks.

This is classic **institutional alternative data**. Quant funds such as
**Two Sigma** and **DE Shaw** have long treated open-source telemetry —
commit cadence, contributor counts, repo activity — as a tradeable signal that
front-runs reported fundamentals. Mycroft Agent 4 builds a lightweight version
of that same idea on free infrastructure:

1. Pull the 10 most-recently-pushed public repos for each watchlist org.
2. Compute weekly velocity metrics (active repos, stars, languages, top repo).
3. Compare against last week's run stored in Supabase → **velocity_direction**.
4. Ask Groq (`llama-3.3-70b-versatile`) to classify activity and momentum.
5. Assemble signals, upsert to Supabase, and emit a markdown report.

### Watchlist

| Ticker | Company   | GitHub Org          |
|--------|-----------|---------------------|
| NVDA   | NVIDIA    | `NVIDIA`            |
| AMD    | AMD       | `GPUOpen-Tools`     |
| INTC   | Intel     | `intel`             |
| GOOGL  | Google    | `google`            |
| AAPL   | Apple     | `apple`             |
| MSFT   | Microsoft | `microsoft`         |
| META   | Meta      | `facebookresearch`  |

---

## 2. Mycroft Architecture

| Agent | Name                          | Status      | Output Table(s)                      |
|-------|-------------------------------|-------------|--------------------------------------|
| 1     | Earnings-Call Anxiety Index   | Live        | `anxiety_runs`                       |
| 2     | Patent Filing Tracker         | Live        | `patent_runs`                        |
| 3     | Media Narrative Monitor       | Live        | `media_narratives_raw`               |
| **4** | **GitHub Commit Velocity Tracker** | **This agent** | **`github_signals`, `github_reports`** |
| 5     | Mindshare / Attention Signal  | Planned     | `mindshare_signals`                  |
| 6     | Contradiction Engine          | Planned     | `contradiction_reports`              |

Agent 4 produces an *engineering activity* lens that Agent 6 cross-references
against narrative and patent signals to surface contradictions (see §12).

---

## 3. The Groq Signals

Groq (`llama-3.3-70b-versatile`, `temperature: 0.1`, `max_tokens: 2000`) returns
a JSON array keyed by ticker. Two classification axes drive the report:

### `activity_classification`
How much engineering throughput the org is currently showing.

| Value           | Meaning                                              |
|-----------------|------------------------------------------------------|
| `HIGHLY_ACTIVE` | Many active repos, broad and fresh push activity     |
| `ACTIVE`        | Healthy, steady engineering output                   |
| `MODERATE`      | Some activity, neither surging nor stalling          |
| `LOW_ACTIVITY`  | Sparse pushes; engineering looks quiet               |

### `momentum_signal`
The *direction* of that activity over time.

| Value         | Meaning                                                  |
|---------------|----------------------------------------------------------|
| `BUILDING`    | Activity ramping up — possible pre-launch acceleration   |
| `MAINTAINING` | Steady-state output                                      |
| `SLOWING`     | Decelerating — fewer fresh pushes than expected          |
| `PIVOTING`    | Activity shifting focus (new repos / language mix shift) |

Each company record also carries `key_observation` (one sentence),
`notable_repos` (1–2 repo names), and `risk_flag` (boolean).

---

## 4. Report Structure

The webhook returns a markdown report with **6 core sections** (plus header,
limitations, and footer):

1. **Executive Summary** — companies tracked, accelerating, stable, decelerating, risk flags.
2. **Engineering Velocity Rankings** — sorted by active repos; per-company velocity, classification, momentum, observation, top repo, notable repos, risk flag.
3. **Accelerating Companies** — those with `velocity_direction = ACCELERATING`.
4. **Risk Flags** — those with `risk_flag = true`.
5. **Week-over-Week Delta Table** — repos this week vs last week, delta, direction.
6. **Language Landscape** — top languages per company.

Followed by **Known Limitations** and the Mycroft footer.

---

## 5. Tech Stack

| Layer        | Technology                              |
|--------------|-----------------------------------------|
| Orchestration| n8n                                     |
| Data source  | GitHub REST API (free, authenticated)   |
| LLM          | Groq — `llama-3.3-70b-versatile`        |
| Storage      | Supabase (Postgres)                     |
| Delivery     | Webhook → markdown report               |

LLM calls go through **HTTP Request nodes** only — no n8n LLM Chain nodes.

---

## 6. Prerequisites

- A running **n8n** instance (self-hosted or cloud), v1.x+.
- A **Supabase** project.
- A free **GitHub Personal Access Token**.
- A free **Groq API key**.
- Environment variables configured on the n8n host (see §8).

---

## 7. Supabase Setup

Run [setup.sql](setup.sql) in the Supabase **SQL Editor**. It creates:

- `github_signals` — one row per company per week (`unique (ticker, run_week)`).
- `github_reports` — one row per run with the rendered markdown.

Both tables have **row level security disabled** for service-key access.
Indexes are created on `ticker`, `velocity_direction`, `risk_flag`, and
`run_timestamp`.

---

## 8. Credentials & Environment Variables

| Variable          | Where to get it                              | Purpose                                  |
|-------------------|----------------------------------------------|------------------------------------------|
| `GITHUB_TOKEN`    | github.com/settings/tokens (free PAT)        | Authenticated GitHub REST API (5k req/hr)|
| `SUPABASE_URL`    | Supabase → Project Settings                  | Supabase REST base URL                   |
| `SUPABASE_KEY`    | Supabase → API settings (service role key)   | Supabase auth (read/upsert/insert)       |
| `GROQ_API_KEY`    | console.groq.com                             | Groq chat completions                    |
| `PIPELINE_SECRET` | any random string you choose                 | Validates `X-Pipeline-Secret` on webhook |

In n8n:

- Set the env vars above on the n8n host so `{{ $env.VAR }}` resolves.
- Create a **Supabase API** credential named **"Supabase Mycroft"** (used by the
  two Supabase nodes) with your project URL + service role key.
- Create an **Header Auth** credential named
  **"Pipeline Secret (X-Pipeline-Secret)"** with header name
  `X-Pipeline-Secret` and value equal to `PIPELINE_SECRET`.

---

## 9. n8n Import Steps

1. Open n8n → **Workflows** → **Import from File**.
2. Select [workflow.json](workflow.json).
3. Open the two Supabase nodes and bind the **"Supabase Mycroft"** credential.
4. Open the **Manual Pipeline Webhook** node and bind the **Header Auth** credential.
5. Confirm the host env vars (`GITHUB_TOKEN`, `GROQ_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `PIPELINE_SECRET`) are set.
6. Save. Leave the workflow **inactive** until you've done a manual test run.

---

## 10. First Run

Trigger the pipeline manually via the webhook:

```bash
curl -H "X-Pipeline-Secret: your-secret" \
  http://localhost:5678/webhook/run-github-pipeline
```

The response body is the full markdown report (`Content-Type: text/markdown`).
The **first run** seeds Supabase and has no week-over-week comparison — every
company shows as `STABLE` with `is_first_run = true`. Subsequent runs compute
real deltas.

The **Cron Trigger** runs automatically every **Sunday 06:00 UTC**.

---

## 11. Known Limitations

- **Top 10 repos per org only** — deeper backlogs are not sampled.
- **Repos delta is an activity proxy, not a raw commit count.**
- **First run has no week-over-week comparison.**
- **GitHub token required** (5,000 req/hr authenticated).

---

## 12. How `github_signals` Feeds Agent 6 (Engineering Silence)

Agent 6 (Contradiction Engine) reads `github_signals` to detect the
**Engineering Silence** pattern: a company that is *loud* in narrative or patent
channels (Agents 2 & 3) but whose public engineering velocity is flat or
decelerating.

Concretely, Agent 6 looks for rows where:

- `velocity_direction = 'DECELERATING'` or `momentum_signal IN ('SLOWING','PIVOTING')`, **and**
- `risk_flag = true`,

while the same ticker shows rising media/patent activity in the other agents'
tables. The mismatch — public optimism with quiet engineering — is logged to
`contradiction_reports` as a high-value contrarian signal. The `run_week`
key makes week-aligned joins across agents straightforward.

---

## 13. Project Structure

```
.
├── workflow.json   # importable n8n workflow (22 nodes)
├── setup.sql       # Supabase schema: github_signals + github_reports
└── README.md       # this file
```

---

_Mycroft — GitHub Commit Velocity Tracker | Agent 4_
_Stack: n8n + GitHub REST API + Groq + Supabase_
