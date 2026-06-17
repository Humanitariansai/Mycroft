# Signal Contradiction Detector — Mycroft Agent 6

## What this synthesis layer does

This is the final synthesis layer of the Mycroft investment-intelligence framework. It reads from all five upstream agent tables simultaneously and runs **contradiction detection** — finding where crowd belief, media narrative, patent velocity, engineering activity, and research footprint tell *different stories* about the same company at the same time. Any single signal in isolation is noise: a Reddit spike, a patent filing, a fresh article. But when five independent data layers — built from entirely different sources — **diverge simultaneously** for the same company within the same seven-day window, that divergence is no longer noise. It is structural, and it is exactly the kind of information asymmetry that precedes mispricing. Agent 6 is what makes the rest of the framework meaningful.

---

## Mycroft architecture

| Agent | Workflow | Table(s) | Signal | Built |
|---|---|---|---|---|
| Agent 1 | Crowd Anxiety | `anxiety_runs` | Crowd behavioral psychology (Reddit / herd detection) | ✅ |
| Agent 2 | Patent Velocity | `patent_runs` | Technology acceleration (filing leaderboard) | ✅ |
| Agent 3 | Media Narrative | `media_narratives_raw` | Information-age scoring (recycled vs. fresh) | ✅ |
| Agent 4 | GitHub Velocity | `github_signals` | Engineering activity (commit/release momentum) | ✅ |
| Agent 5 | Research Mindshare | `mindshare_signals` | Research footprint (Wikipedia + academic) | ✅ |
| **Agent 6** | **Signal Contradiction Detector** | `contradiction_reports`, `contradiction_run_reports` | **Cross-signal divergence synthesis — reads all 5 above** | ✅ |

Agent 6 sits at the bottom, reading every upstream table and writing only its own two `contradiction_*` tables.

---

## The 5 contradiction patterns

| Pattern | Signals involved | What it means |
|---|---|---|
| **Engineering Silence** | GitHub + Media | Media is publishing fresh, positive narratives while engineering activity is *decelerating*. The story may be ahead of the reality. |
| **Mindshare Gap** | Mindshare + Crowd | Wikipedia knowledge activity is spiking but the retail crowd hasn't noticed. An information-asymmetry window — institutional awareness before retail awareness. |
| **Patent-Conference Divergence** | Patents + Mindshare | Filing patents fast but absent from / following at top research conferences. Suggests defensive or stealth R&D rather than open academic contribution. |
| **Narrative Recycling Trap** | Media + Crowd | The crowd is piling into a company saturating the media cycle — but the narrative is mostly *recycled*. Old information being treated as new signal. |
| **Five-Layer Divergence** | All 5 | At least 3 of the 5 independent signal layers disagree on direction. Maximum uncertainty — high-conviction positions are structurally unsupported. |

---

## Contradiction levels

Each company is assigned a level based on its `contradiction_score`:

| Level | Score | Reading |
|---|---|---|
| **CRITICAL** | ≥ 6 | Multiple high-severity contradictions — the signal layers strongly disagree. |
| **ELEVATED** | ≥ 3 | Meaningful divergence worth monitoring. |
| **NOTABLE** | ≥ 1 | At least one pattern triggered. |
| **CLEAN** | 0 | All available signals are aligned. |

---

## How the scoring works

Every triggered pattern contributes points according to its severity:

| Severity | Points |
|---|---|
| HIGH | 3 |
| MEDIUM | 2 |
| LOW | 1 |

`contradiction_score` = sum of points across all triggered patterns. Companies are then ranked by score descending, and the level thresholds above are applied.

---

## Tech stack

| Component | Used for |
|---|---|
| **n8n** | Orchestration (cron + manual webhook, parallel reads, merge, code nodes) |
| **Supabase (Postgres)** | Reads 5 upstream tables; writes 2 contradiction tables |
| **Groq — `llama-3.3-70b-versatile`** | Narrative synthesis of detected contradictions |

> **No new external APIs.** Agent 6 purely reads from Supabase and calls Groq. It introduces zero new data sources — all raw signal collection happened in Agents 1–5.

---

## Prerequisites

**All five upstream agents must have run at least once** before Agent 6 can produce meaningful output. Contradiction detection requires multiple independent signals to function: a pattern is only evaluated when every signal it depends on has data. If, say, `github_signals` is empty, the Engineering Silence and Five-Layer patterns that depend on it simply won't trigger — the run won't crash, but coverage will be partial. The richer the upstream tables, the more patterns surface.

---

## Supabase setup

Run the schema once against your Supabase project:

```bash
psql "$SUPABASE_DB_URL" -f setup.sql
```

…or paste `setup.sql` into the Supabase SQL editor. It creates `contradiction_reports` and `contradiction_run_reports`, the supporting indexes, and disables RLS on both. The five upstream tables are owned by their respective agents and are **not** (re)created here — `setup.sql` includes them only as a reference comment.

---

## Credentials

| Credential | n8n env var | Where to get |
|---|---|---|
| Supabase URL | `SUPABASE_URL` | Supabase project settings |
| Supabase key | `SUPABASE_KEY` | Supabase API settings |
| Groq API key | `GROQ_API_KEY` | console.groq.com |
| Pipeline secret | `PIPELINE_SECRET` | Any random string |

Configure the Supabase credential in n8n (used by all 5 read nodes and both write nodes) and the header-auth credential (`X-Pipeline-Secret`) for the manual webhook.

---

## Important: run order

Agent 6 is scheduled **weekly on Tuesday at 08:00 UTC**, deliberately *after* the upstream agents have refreshed their data:

| Day | Agent | Refreshes |
|---|---|---|
| Sunday | Agent 4 | `github_signals` |
| Monday | Agent 5 | `mindshare_signals` |
| **Tuesday 08:00 UTC** | **Agent 6** | **Reads all 5, detects contradictions** |

This ordering guarantees the engineering and research footprints are fresh before contradiction detection runs.

---

## First run

Trigger the pipeline manually via the webhook:

```bash
curl -H "X-Pipeline-Secret: your-secret" \
  http://localhost:5678/webhook/run-contradiction-pipeline
```

The response body is the full markdown contradiction report (`Content-Type: text/markdown`).

---

## Known limitations

- **Graceful degradation:** When upstream agents haven't run, missing signals are logged and any pattern requiring that signal is skipped — the run completes with partial coverage rather than failing.
- **Empirical thresholds:** Pattern thresholds (age-score cutoffs, footprint levels, delta percentages) are empirically chosen, *not* statistically validated against price outcomes.
- **Groq scope:** LLM analysis is limited to the **top 5 companies by contradiction score** to manage token usage; lower-scoring companies still appear in the report from rule-based detection but without an LLM narrative.
- **Cold start:** The first few weeks will produce limited patterns as the upstream tables fill up.

---

## Project structure

```
signal-contradiction-detector/
├── workflow.json
├── setup.sql
└── README.md
```

---

*Mycroft — Signal Contradiction Detector | Agent 6*
*Stack: n8n + Groq (llama-3.3-70b) + Supabase*
*Reads: anxiety_runs, patent_runs, media_narratives_raw, github_signals, mindshare_signals*
*For research and educational purposes only — not financial advice.*
