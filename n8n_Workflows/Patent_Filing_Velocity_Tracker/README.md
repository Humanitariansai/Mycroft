# Patent Filing Velocity Tracker — Mycroft Analytical Agent

A production-ready n8n workflow that tracks patent filing acceleration across the five largest US AI chip companies (NVIDIA, AMD, Intel, Google, Apple) using free USPTO PatentsView data, runs six parallel Claude analyses against each run, and emits structured intelligence signals to the [Mycroft](https://www.humanitarians.ai/mycroft) orchestration layer.

This workflow is one **Mycroft Analytical Agent**. Mycroft is an open-source AI-powered investment intelligence framework being built by [Humanitarians AI](https://www.humanitarians.ai). The agent's job is to detect strategic intent through patent velocity — a leading indicator of company direction that becomes visible months before product announcements or analyst coverage — and surface it as machine-readable signals (`PATENT_VELOCITY`, with `investmentSignal`, `breakthroughScore`, and `expiresAt`) that other Mycroft components can compose with signals from market data, hiring trends, supply-chain disclosures, and earnings.

---

## The 7 signals extracted

| # | Signal | Output shape | Question it answers |
|---|--------|--------------|----------------------|
| 1 | **Velocity Score** | `[{ company, velocityScore, trend, insight, confidenceLevel }]` | Who is filing faster than they were, calibrated to absolute volume? |
| 2 | **Concept Novelty** | `[{ company, newConcepts, emergingThemes, noveltyScore, confidenceLevel }]` | What technical vocabulary appears in this run but not the last? |
| 3 | **Inventor Network** | `[{ company, newInventorCount, teamExpansionSignal, insight, confidenceLevel }]` | Are research teams expanding, stable, or contracting? |
| 4 | **Cross-Company Convergence** | `{ convergenceTopics, divergenceTopics, leaderByCategory, strategicInsight, confidenceLevel }` | Where is the field consolidating? Where is one player going it alone? |
| 5 | **Strategic Intent** | `[{ company, intent, confidence, reasoning, keyTechnicalThemes }]` | Defensive / Expansive / Foundational / Incremental / Exploratory? |
| 6 | **Breakthrough Detection** | `[{ company, breakthroughPatents, breakthroughScore, confidenceLevel }]` | Is anyone filing in CPC subcodes they've never touched before? |
| 7 | **Investment Signal** (derived) | per company: `ACCUMULATE / WATCH / HOLD / REDUCE / INSUFFICIENT_DATA` with `signalExpiresAt` | One composite, machine-readable bucket per company for downstream orchestration. |

The 7th signal is **derived locally** from the other six inside the Signal Aggregator node — no separate Claude call. Rules:
- `ACCUMULATE`: `velocityScore > 70` AND `trend === 'ACCELERATING'` AND `teamExpansionSignal === 'EXPANDING'`
- `WATCH`: `breakthroughScore > 60`
- `HOLD`: `trend === 'STEADY'`
- `REDUCE`: `trend === 'DECELERATING'`
- `INSUFFICIENT_DATA`: any core signal is `null` or any company had fewer than 5 patents in the date range

Every signal carries `signalExpiresAt` set to 90 days from the run timestamp — downstream consumers must treat older signals as stale.

---

## Tech stack

| Layer | Tool | Notes |
|-------|------|-------|
| Orchestration | n8n | self-hosted via `npx n8n` |
| Patent data | USPTO PatentsView API | free, no auth, ~18 month publication lag |
| LLM | Claude Sonnet (`claude-sonnet-4-6`) | 7 parallel chains (6 analysis + 1 newsletter), 1500 max tokens |
| Storage | Supabase (Postgres + JSONB) | 3 tables: `patent_runs`, `newsletter_runs`, `error_log` |
| Email | SendGrid **or** n8n native email node | drives the weekly subscriber briefing |
| Downstream | Mycroft orchestration endpoint | HTTP POST with normalized signal payload |

---

## Prerequisites

- **Node.js 18+** (for `npx n8n`)
- **n8n** running locally or self-hosted
- **Supabase** project (free tier is sufficient)
- **Anthropic API key** — https://console.anthropic.com
- **SendGrid account** (or any SMTP credentials you'd rather use for the n8n email node)

---

## 1. Supabase setup

Open the Supabase SQL editor and run **all three** statements:

```sql
create table patent_runs (
  id uuid default gen_random_uuid() primary key,
  created_at timestamptz default now(),
  date text,
  timestamp text,
  leaderboard jsonb,
  convergence jsonb,
  quarterly_stats jsonb,
  total_patents_analyzed integer,
  agent_metadata jsonb
);

create table newsletter_runs (
  id uuid default gen_random_uuid() primary key,
  created_at timestamptz default now(),
  run_id uuid references patent_runs(id),
  subject text,
  body text,
  sent_to integer,
  status text
);

create table error_log (
  id uuid default gen_random_uuid() primary key,
  created_at timestamptz default now(),
  run_id uuid,
  node_name text,
  error_type text,
  error_detail jsonb
);
```

Then disable RLS on the three tables so the anon key can write:

```sql
alter table patent_runs disable row level security;
alter table newsletter_runs disable row level security;
alter table error_log disable row level security;
```

Re-enable RLS and route writes through a service-role key from a backend if you ever expose this Supabase project publicly.

You'll also need a `newsletter_subscribers` table for the briefing branch — the workflow queries it for the `email` column:

```sql
create table newsletter_subscribers (
  id uuid default gen_random_uuid() primary key,
  created_at timestamptz default now(),
  email text unique not null
);
alter table newsletter_subscribers disable row level security;
```

---

## 2. Credential placeholders

Find-and-replace these inside `workflow.json` before importing:

| Placeholder | Source | Replace with |
|-------------|--------|--------------|
| `YOUR_SUPABASE_URL` | Supabase project settings | `https://abcdxyz.supabase.co` |
| `YOUR_SUPABASE_ANON_KEY` | Supabase project settings | the anon JWT |
| `YOUR_ANTHROPIC_API_KEY` | Anthropic console | stored inside the n8n credential, not in the file |
| `YOUR_ANTHROPIC_CREDENTIAL_NAME` | n8n credentials UI | e.g. `Anthropic account` |
| `YOUR_ANTHROPIC_CREDENTIAL_ID` | n8n credentials UI | auto-assigned when you save the credential |
| `YOUR_SMTP_CREDENTIAL_NAME` / `YOUR_SMTP_CREDENTIAL_ID` | n8n SMTP / SendGrid credential | for the Send Email node |
| `YOUR_PIPELINE_SECRET` (n8n env var `PIPELINE_SECRET`) | you choose | a random string used as the `X-Pipeline-Secret` header |
| `YOUR_MYCROFT_ORCHESTRATION_ENDPOINT` + `YOUR_AGENT_SECRET` | Mycroft team | the agent-bus URL and per-agent secret |

---

## 3. n8n import

```bash
npx n8n
```

In the n8n UI (default `http://localhost:5678`):

1. **Workflows → Import from File →** select `workflow.json`.
2. **Credentials → New → Anthropic API**. Paste your key. Save. Open the workflow and bind the credential to each of the **7 Anthropic Model** nodes (Anthropic Model 1–6 plus Anthropic Model Newsletter).
3. **Credentials → New → SMTP** (or SendGrid). Bind to the **Send Email** node.
4. Activate the workflow.

---

## 4. Environment variables

Set the pipeline secret as an n8n environment variable. For local `npx n8n`:

```bash
export PIPELINE_SECRET=your-long-random-string
npx n8n
```

For Docker, add `-e PIPELINE_SECRET=...`. The Security Gate code node reads it via `$env.PIPELINE_SECRET` and rejects any request whose `X-Pipeline-Secret` header doesn't match.

> The webhook URL is publicly reachable once the workflow is active. The secret header is the **only** authentication in front of the pipeline — pick a long random value.

---

## 5. First run

```bash
curl -H "X-Pipeline-Secret: $PIPELINE_SECRET" http://localhost:5678/webhook/run-patent-pipeline
```

The pipeline takes roughly 60–120s: fetch previous-run baseline + PatentsView fetch (in parallel), structural clean, classify + quality-weight, patent-count gate, six parallel Claude analyses, merge, signal aggregator (derives `investmentSignal` + `signalExpiresAt`), then three parallel branches:
- **Persistence** — insert to `patent_runs` (`Prefer: return=representation` gives us the new row id), write any `pendingErrors` and `fetchErrors` to `error_log`.
- **Newsletter** — gated on `totalPatentsAnalyzed >= 200`. Generates the ~400-word briefing with Claude, sends to all subscribers, records into `newsletter_runs`. Skipped runs log a `NEWSLETTER_SKIPPED` row to `error_log`.
- **Mycroft emit** — POST to `YOUR_MYCROFT_ORCHESTRATION_ENDPOINT` with the normalized signals payload.

The three branches converge into a `Merge waitForAll, numberInputs: 3` node, then the workflow responds to the original webhook with summary JSON.

---

## Webhook URL

```
http://localhost:5678/webhook/run-patent-pipeline
```

Requires `X-Pipeline-Secret` header. Returns 401 if missing/wrong.

---

## Adding newsletter subscribers

Insert directly via the Supabase SQL editor or REST:

```sql
insert into newsletter_subscribers (email) values
  ('researcher1@example.com'),
  ('researcher2@example.com');
```

Or via PostgREST:

```bash
curl -X POST "$SUPABASE_URL/rest/v1/newsletter_subscribers" \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"new@example.com"}'
```

---

## Mycroft orchestration endpoint

`YOUR_MYCROFT_ORCHESTRATION_ENDPOINT` is a **placeholder** until the Mycroft agent bus is live. Until then either:
1. Replace it with `https://httpbin.org/post` (or any null endpoint) and ignore the response — the workflow logs non-2xx but does not fail.
2. Disable that branch by removing the connection from `Signal Aggregator → Mycroft Orchestration Emit` and reducing `Converge Outputs.numberInputs` from 3 to 2.

When the bus is ready, replace the placeholder with the production URL and rotate `YOUR_AGENT_SECRET`.

The emitted payload shape:

```json
{
  "agentName": "PatentVelocityAgent",
  "agentVersion": "1.0",
  "runId": "<uuid from patent_runs insert>",
  "timestamp": "<iso>",
  "signals": [
    {
      "company": "NVIDIA",
      "signalType": "PATENT_VELOCITY",
      "direction": "ACCELERATING",
      "strength": 87,
      "confidence": 0.82,
      "investmentSignal": "ACCUMULATE",
      "breakthroughScore": 64,
      "expiresAt": "<iso, +90 days>"
    }
  ]
}
```

---

## Known limitations

1. **USPTO shows published patents, not filed.** PatentsView exposes the grant/publication date, which lags the filing date by roughly 18 months. Treat velocity as a medium-term trend signal, not real-time news.
2. **Assignee IDs are placeholders.** `nvidia-assignee-id`, `amd-assignee-id`, etc. must be replaced with real PatentsView assignee identifiers before the first run. Look them up at https://patentsview.org/query/builder by searching the company name and inspecting the returned `assignee_id`. The workflow will fall back to alias string matching if the assignee_id query returns zero, but that path is noisier.
3. **Company name normalization is incomplete for subsidiaries.** Aliases are hardcoded (e.g. `Alphabet`, `DeepMind`, `Google DeepMind Technologies Limited`). Acquisitions, joint ventures, and historical assignee strings outside that list are missed.
4. **CPC scope may exclude relevant subcodes.** Currently `G06N` and `H01L` only. Neighboring areas (`G06F` general computing, `G11C` memory, parts of `H03K`) are out of scope and won't influence velocity numbers.
5. **Concept novelty requires 2+ runs to be meaningful.** The first run has empty `previousConcepts`, so Claude 2 scores by within-batch dominance instead of true newness. Trust the signal only from the second run onward.
6. **Signal Aggregator field-matching fails silently on unexpected Claude output shapes.** Each of the six outputs is identified by key presence (`velocityScore`+`trend`, `noveltyScore`, `teamExpansionSignal`, etc.). If a Claude response drifts schema, that signal silently defaults to empty — a row is written to `error_log` with `error_type: 'UNRECOGNISED_SHAPE'` but the pipeline continues.
7. **Strategic intent stability across runs is unvalidated.** Claude 5 classifies each company into one of five buckets per run, but no cross-run drift check exists. Treat single-run intent with caution; trust patterns that persist across multiple runs.
8. **Investment signal is experimental and is not financial advice.** The `ACCUMULATE / WATCH / HOLD / REDUCE` mapping is a deterministic rule derived from the other six signals for downstream orchestration. It is **not** a recommendation. Do not deploy capital on the basis of this output.
9. **Newsletter is skipped when `totalPatentsAnalyzed < 200`.** Below that threshold the briefing would be too thin to be useful. The skip is logged to `error_log` with `error_type: 'NEWSLETTER_SKIPPED'`.
10. **Mycroft orchestration endpoint is a placeholder** until the agent bus is built. The HTTP node is wired but writes to `YOUR_MYCROFT_ORCHESTRATION_ENDPOINT`. The pipeline does not fail on a non-2xx response from this branch — failures land in `error_log` instead.
11. **PatentsView fetch uses page 1 / 100 results per alias only.** Companies with more than ~100 matching patents per assignee_id in the 2-year window will be truncated. Add pagination if you extend the scope.

---

## Project structure

```
Patent_Filing_Velocity_Tracker/
├── workflow.json    # n8n workflow — Settings → Import Workflow
├── setup.sql        # Supabase schema (3 tables + subscribers)
└── README.md        # this file
```

---

## Contributing

Mycroft is an open-source Humanitarians AI project. PRs and issues are welcome on the project repository — see https://www.humanitarians.ai/mycroft for the latest entry point. When proposing changes to this agent:

- Bump `agentVersion` and `promptVersion` in the Signal Aggregator code if you change any Claude prompt.
- Add a row to `error_log` for any new failure mode rather than throwing — the orchestration layer expects the agent to always respond.
- Don't add new signals without extending the field-detection logic in the Signal Aggregator; new shapes that aren't recognized are silently dropped.

---

## License

Open source under the [Humanitarians AI](https://www.humanitarians.ai) project umbrella. Patent data is sourced from the public USPTO PatentsView API and is in the public domain. Claude outputs derived from this data are governed by Anthropic's usage policies.
