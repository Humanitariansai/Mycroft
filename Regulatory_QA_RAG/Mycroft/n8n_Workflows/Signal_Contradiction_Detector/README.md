# Signal Contradiction Detector

Any single signal is noise. A Reddit anxiety spike might be panic or might be a meme. A patent filing might signal strategic intent or might be defensive IP protection. A fresh media article might carry new information or might be recycled narrative in new language. Individually, none of these signals is reliable enough to act on.

But when five independent data layers — built from entirely different sources, measuring entirely different things — **diverge simultaneously** for the same company within the same seven-day window, that divergence is no longer noise. It is structural. It is exactly the kind of information asymmetry that precedes mispricing.

The Signal Contradiction Detector reads from all five upstream signal tables simultaneously and runs cross-signal contradiction detection. It finds where crowd belief, media narrative, patent velocity, engineering activity, and research footprint tell different stories about the same company. The output is a structured markdown contradiction report ranked by severity, with Groq-written narrative explaining what each contradiction means.

No new data sources. Purely reads from Supabase and calls Groq.

---

## Upstream Signals

This workflow reads from five tables produced by five upstream agents. All five must have run at least once before this workflow produces meaningful output.

| Agent | Signal | Table |
|---|---|---|
| [Reddit Anxiety Index](https://github.com/humanitarians-ai/mycroft/tree/main/reddit-anxiety-index) | Crowd behavioral psychology — anxiety score, herd detection | `anxiety_runs` |
| [Patent Velocity Tracker](https://github.com/humanitarians-ai/mycroft/tree/main/patent-velocity-tracker) | Technology acceleration — patent filing leaderboard, trend | `patent_runs` |
| [Media Narrative Tracker](https://github.com/humanitarians-ai/mycroft/tree/main/media-narrative-tracker) | Information age scoring — novel vs recycled, companies mentioned | `media_narratives_raw` |
| [GitHub Commit Velocity Tracker](https://github.com/humanitarians-ai/mycroft/tree/main/github-commit-velocity-tracker) | Engineering activity — velocity direction, momentum signal, risk flag | `github_signals` |
| [Research Footprint Monitor](https://github.com/humanitarians-ai/mycroft/tree/main/research-footprint-monitor) | Research presence — footprint score, Wikipedia edit velocity, academic signal | `mindshare_signals` |

---

## The 5 Contradiction Patterns

### Pattern 1 — Engineering Silence
**Signals:** GitHub Velocity + Media Narrative

Triggered when `github_signals.velocity_direction = DECELERATING` and the average `information_age_score` for media articles mentioning the same company is above 60.

Media is publishing fresh, positive narratives while engineering activity is quietly slowing. The story the market is hearing may be ahead of the reality on the ground.

Severity: HIGH if `delta_pct < -20`, otherwise MEDIUM.

---

### Pattern 2 — Mindshare Gap
**Signals:** Research Footprint + Reddit Anxiety

Triggered when `mindshare_signals.is_spike = true` (Wikipedia edits spiking) and the company does not appear in `anxiety_runs.herd_detection` tickers in the last 7 days.

Public knowledge activity is surging — editors are updating what people know about this company — but the retail crowd hasn't noticed yet. An information asymmetry window between institutional awareness and retail awareness.

Severity: HIGH if `footprint_score > 70`, otherwise MEDIUM.

---

### Pattern 3 — Patent-Conference Divergence
**Signals:** Patent Velocity + Research Footprint

Triggered when `patent_runs` leaderboard shows `trend = ACCELERATING` for a company and `mindshare_signals.academic_signal` is `ABSENT` or `FOLLOWING`.

The company is filing patents fast — building something — but is not presenting research at top conferences. Suggests defensive or stealth R&D rather than open academic contribution. The gap between what a company is protecting and what it's publishing is itself a signal.

Severity: HIGH if `velocity_score > 70`, otherwise LOW.

---

### Pattern 4 — Narrative Recycling Trap
**Signals:** Media Narrative + Reddit Anxiety

Triggered when the average `information_age_score` for articles mentioning a company is below 35, and the company appears in `anxiety_runs.herd_detection` tickers.

The retail crowd is piling into a company saturating the media cycle — but the underlying media narrative is mostly recycled old information dressed in new language. The crowd is reacting as if a story is new when it isn't.

Severity: HIGH if `recycled_pct > 0.7`, otherwise MEDIUM.

---

### Pattern 5 — Five-Layer Divergence
**Signals:** All 5

Maps each signal to a direction (BULLISH / BEARISH / NEUTRAL) and triggers when 3 or more of the 5 signals conflict.

| Signal | BULLISH | BEARISH |
|---|---|---|
| Crowd (anxiety) | anxiety_score < 40 | anxiety_score > 60 |
| Patents | trend = ACCELERATING | trend = DECELERATING |
| Media | avg_age_score > 60 | avg_age_score < 35 |
| GitHub | velocity = ACCELERATING | velocity = DECELERATING |
| Research | footprint_score > 60 | footprint_score < 30 |

Maximum uncertainty — five independent data layers cannot agree on what is happening with this company. High-conviction positions in either direction are structurally unsupported.

Severity: HIGH if ≥ 4 signals conflict, otherwise MEDIUM.

---

## Contradiction Levels

| Level | Score | Meaning |
|---|---|---|
| CRITICAL | ≥ 6 | Multiple high-severity contradictions — layers strongly disagree |
| ELEVATED | ≥ 3 | Meaningful divergence worth monitoring |
| NOTABLE | ≥ 1 | At least one pattern triggered |
| CLEAN | 0 | All available signals are aligned |

**Scoring:** HIGH pattern = 3 pts · MEDIUM = 2 pts · LOW = 1 pt

---

## Architecture

```
Cron Trigger (weekly, Tuesday 08:00 UTC)
  +
Manual Webhook  GET /run-contradiction-pipeline
  ↓
Fetch Watchlist
  ↓
5 parallel Supabase reads
  Read anxiety_runs       (last 7 days)
  Read patent_runs        (latest 5 runs)
  Read media_narratives_raw (last 7 days)
  Read github_signals     (latest 14 rows — 2 runs × 7 companies)
  Read mindshare_signals  (latest 7 rows — most recent run)
  ↓
Merge All Signals  (append, 5 inputs)
  ↓
Normalize Signal Data
  (groups appended rows by ticker, maps fields by source table)
  ↓
Detect Contradiction Patterns
  (runs all 5 patterns per company, assigns severity)
  ↓
Score Contradictions
  (sums severity points, assigns level, sorts by score desc)
  ↓
Aggregate for Groq
  (top 5 companies by contradiction score)
  ↓
Groq: Contradiction Analyst  (llama-3.3-70b-versatile)
  ↓
Parse Groq Response
  ↓
Assemble Contradiction Report Data
  ↓
Upsert to Supabase  (conflict: ticker, run_week)
  ↓
Generate Report
  ↓
Store Full Report in Supabase
  ↓
Pipeline Response  (Content-Type: text/markdown)
```

---

## Report Structure

Every run produces a markdown report with five sections:

1. **Executive Summary** — companies analyzed, critical count, elevated count, clean count, total patterns detected
2. **Critical Contradictions** — per-company: contradiction narrative, most significant pattern, investor implication, confidence, pattern list with severities, signal direction table, data gaps
3. **Elevated Contradictions** — same format, lower severity
4. **Pattern Frequency This Week** — how many times each pattern triggered and which companies
5. **Signal Availability This Run** — which of the 5 upstream tables had data vs were empty

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | n8n (self-hosted) |
| Signal input | 5 Supabase tables (read-only) |
| LLM | Groq — `llama-3.3-70b-versatile` via HTTP Request node |
| Storage | Supabase (PostgreSQL) |
| Output | Markdown report via webhook + archived in Supabase |

---

## Prerequisites

- n8n instance running (self-hosted, v1.x+)
- Supabase project with all 5 upstream tables populated
- Groq API key — [console.groq.com](https://console.groq.com)
- All 5 upstream agents must have run at least once

---

## Supabase Setup

Run `setup.sql` in the Supabase SQL Editor before the first run. It creates:

- `contradiction_reports` — one row per company per week, unique on `(ticker, run_week)`
- `contradiction_run_reports` — full markdown report archive per run
- Indexes on `ticker`, `run_week`, `contradiction_level`, `contradiction_score`

The 5 upstream tables are not created here — they are owned by their respective agents.

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
- A **Supabase** credential and bind it to all 5 read nodes and both write nodes
- A **Header Auth** credential (`X-Pipeline-Secret` = your `PIPELINE_SECRET`) and bind it to the Manual Pipeline Webhook node

---

## Import & Activate

1. n8n → **Workflows → Import from File** → select `workflow.json`
2. Open all 5 **Read** nodes → bind your Supabase credential
3. Open **Insert to Supabase** and **Store Full Report** → bind your Supabase credential
4. Open **Manual Pipeline Webhook** → bind your Header Auth credential
5. After import: open **Merge All Signals** → confirm Mode is set to **Append**, numberInputs = **5**
6. Save — leave inactive until you've done a manual test run

---

## Run Order

This workflow is scheduled for Tuesday 08:00 UTC — deliberately after the upstream agents refresh their data:

| Day | Agent | Table refreshed |
|---|---|---|
| Sunday 06:00 UTC | GitHub Commit Velocity | `github_signals` |
| Monday 07:00 UTC | Research Footprint Monitor | `mindshare_signals` |
| Tuesday 08:00 UTC | **Signal Contradiction Detector** | reads all 5 |

Do not activate this workflow before all 5 upstream workflows have run at least once.

---

## First Run

```bash
curl -H "X-Pipeline-Secret: your-secret" \
  http://localhost:5678/webhook/run-contradiction-pipeline
```

The full markdown report is returned directly in the response. The first run with empty upstream tables will show all signals as unavailable and no patterns triggered — this is expected. Run all 5 upstream workflows first, then run this.

---

## Known Limitations

- **Graceful degradation** — when an upstream table is empty, patterns requiring that signal are skipped. The run completes with partial coverage rather than failing.
- **Empirical thresholds** — pattern trigger conditions are empirically defined, not statistically validated against price outcomes.
- **Groq scope** — LLM narrative analysis is limited to the top 5 companies by contradiction score. Lower-scoring companies still appear in the report from rule-based detection but without an LLM narrative.
- **Cold start** — the first few weeks produce limited patterns as upstream tables fill up with historical data.

---

## Project Structure

```
signal-contradiction-detector/
├── workflow.json
├── setup.sql
└── README.md
```

---

## Sample Output

```
# Signal Contradiction Detector — Report
**Run ID:** c1e5a9f2-4d6b-4c8e-af3d-5e6f7a8b9c0d
**Generated:** 2026-06-17T08:09:55.220Z
**Signals read:** anxiety_runs · patent_runs · media_narratives_raw
  · github_signals · mindshare_signals

---

## Executive Summary

| Metric | Value |
|---|---|
| Companies analyzed | 7 |
| Critical contradictions | 1 |
| Elevated contradictions | 2 |
| Notable | 1 |
| Clean signals | 3 |
| Patterns detected total | 6 |

---

## Critical Contradictions

### Intel (INTC) — Score: 7 — CRITICAL

**Contradiction narrative:** Intel presents a rare case of five-layer
divergence — media coverage is publishing fresh narratives about AI
PC momentum, patent filings are accelerating in GPU-adjacent IP, yet
GitHub engineering is decelerating sharply, academic research presence
has been absent for two consecutive weeks, and retail sentiment shows
no awareness of the positive media cycle. The divergence between the
IP layer and the engineering layer is particularly stark.

**Most significant pattern:** Engineering Silence — media age score of
71 against a GitHub velocity direction of DECELERATING with a -22.4%
delta. The public narrative is running well ahead of observable
engineering output.

**Investor implication:** High-confidence positions in either direction
are structurally unsupported. The contradictions suggest a period of
internal strategic realignment that has not yet resolved into a clear
directional signal.

**Confidence:** MEDIUM

**Patterns detected:**
  - [HIGH] Engineering Silence: Media avg age score 71, GitHub
    velocity DECELERATING (-22.4%)
  - [HIGH] Patent-Conference Divergence: Patent trend ACCELERATING,
    academic signal ABSENT for 2 consecutive weeks
  - [MEDIUM] Five-Layer Divergence: 4 of 5 signals conflict

**Signal directions:**
| Signal | Direction |
|---|---|
| Crowd (Reddit) | NEUTRAL |
| Technology (Patents) | BULLISH |
| Media narrative | BULLISH |
| Engineering (GitHub) | BEARISH |
| Research (Footprint) | BEARISH |

**Data gaps:** patent_runs leaderboard entry missing velocityScore field

---

## Elevated Contradictions

### NVIDIA (NVDA) — Score: 4 — ELEVATED

**Contradiction narrative:** NVIDIA's Wikipedia edit spike and GitHub
acceleration are not yet reflected in Reddit crowd activity — the
retail herd has not converged on the company this week despite
institutional-facing signals suggesting an imminent announcement.

**Most significant pattern:** Mindshare Gap — Wikipedia spike of 18
edits across 9 editors with no corresponding Reddit herd detection.

**Investor implication:** Monitor closely over the next 48–72 hours
for retail crowd catchup to the Wikipedia activity signal.

**Confidence:** HIGH

**Patterns detected:**
  - [HIGH] Mindshare Gap: Wikipedia is_spike=true, not in Reddit
    herd_detection tickers
  - [LOW] Patent-Conference Divergence: ACCELERATING patents,
    CONTRIBUTING academic signal

---

## Clean Signals

- GOOGL — Google — all signals aligned
- MSFT — Microsoft — all signals aligned
- META — Meta — all signals aligned

---

## Pattern Frequency This Week

| Pattern | Triggers | Companies |
|---|---|---|
| Engineering Silence | 1 | INTC |
| Mindshare Gap | 1 | NVDA |
| Patent-Conference Divergence | 2 | INTC, NVDA |
| Narrative Recycling Trap | 0 | — |
| Five-Layer Divergence | 1 | INTC |

---

## Signal Availability This Run

| Signal | Available | Source table |
|---|---|---|
| Crowd psychology | ✓ | anxiety_runs |
| Patent velocity | ✓ | patent_runs |
| Media narrative | ✓ | media_narratives_raw |
| Engineering activity | ✓ | github_signals |
| Research footprint | ✓ | mindshare_signals |
```

---

## Author

**Sahiti Nallamolu**

- LinkedIn: [linkedin.com/in/sahitinallamolu](https://www.linkedin.com/in/sahitinallamolu/)
- Humanitarians AI Fellow

---

*Stack: n8n + Groq (llama-3.3-70b-versatile) + Supabase*
*For research and educational purposes only — not financial advice.*

---