# Patent Filing Velocity Tracker

Patent filings are a leading indicator. When a company accelerates its filing rate in a specific technical area, it signals a strategic bet being placed months — sometimes years — before the product ships or the analyst report is written. The filing date precedes the publication date by roughly 18 months on the USPTO system, and it precedes the press release by even longer.

This workflow tracks patent filing acceleration across five AI chip companies — NVIDIA, AMD, Intel, Google, and Apple — using free USPTO PatentsView data. Every run fetches recent patents, runs six parallel Claude analyses to extract structured signals, and returns a JSON response containing per-company intelligence: who is filing faster, what new technical concepts are appearing, whether research teams are expanding, where the field is converging, and which companies are filing in territory they've never touched before.

---

## The 7 Signals

| # | Signal | Output shape | Question it answers |
|---|---|---|---|
| 1 | **Velocity Score** | `{ company, velocityScore, trend, insight, confidenceLevel }` | Who is filing faster than they were, calibrated to absolute volume? |
| 2 | **Concept Novelty** | `{ company, newConcepts, emergingThemes, noveltyScore, confidenceLevel }` | What technical vocabulary appears in this run but not the last? |
| 3 | **Inventor Network** | `{ company, newInventorCount, teamExpansionSignal, insight, confidenceLevel }` | Are research teams expanding, stable, or contracting? |
| 4 | **Cross-Company Convergence** | `{ convergenceTopics, divergenceTopics, leaderByCategory, strategicInsight }` | Where is the field consolidating? Where is one player going it alone? |
| 5 | **Strategic Intent** | `{ company, intent, confidence, reasoning, keyTechnicalThemes }` | Defensive / Expansive / Foundational / Incremental / Exploratory? |
| 6 | **Breakthrough Detection** | `{ company, breakthroughPatents, breakthroughScore, confidenceLevel }` | Is anyone filing in CPC subcodes they've never touched before? |
| 7 | **Investment Signal** (derived) | `{ company, investmentSignal, signalExpiresAt }` | One composite signal per company for downstream use |

Signal 7 is derived locally inside the Signal Aggregator node — no separate Claude call:

- `ACCUMULATE` — `velocityScore > 70` AND `trend = ACCELERATING` AND `teamExpansionSignal = EXPANDING`
- `WATCH` — `breakthroughScore > 60`
- `HOLD` — `trend = STEADY`
- `REDUCE` — `trend = DECELERATING`
- `INSUFFICIENT_DATA` — any core signal is null or fewer than 5 patents in the date range

Every signal carries `signalExpiresAt` set to 90 days from the run timestamp.

---

## Architecture

```
Webhook Trigger  GET /run-patent-pipeline
  (Header auth: X-Pipeline-Secret)
  ↓
Security Gate  (validates PIPELINE_SECRET)
  ↓
IF Authorized
  ↓
Fetch Previous Run + Fetch Patent Data  (parallel)
  USPTO PatentsView API — free, no auth
  5 companies × multiple CPC subcodes (G06N, H01L)
  ↓
Merge Fetch Outputs
  ↓
1A: Structural Clean
  ↓
1B: Classify + Quality Weight
  ↓
Patent Count Gate
  (skips Claude analysis if < 5 patents per company)
  ↓
Aggregate for Claude
  ↓
6 parallel Claude analyses  (claude-sonnet-4-6, 1500 tokens each)
  Claude 1: Velocity Score
  Claude 2: Concept Novelty
  Claude 3: Inventor Network
  Claude 4: Cross-Company Convergence
  Claude 5: Strategic Intent
  Claude 6: Breakthrough Detection
  ↓
Merge Claude Outputs  (append, 6 inputs)
  ↓
Signal Aggregator
  (derives Investment Signal + signalExpiresAt)
  ↓
3 parallel branches:

  Persistence branch             Newsletter branch          Orchestration branch
  Insert to patent_runs          Gated: ≥ 200 patents       POST to external endpoint
  Write errors to error_log      Generate newsletter         (placeholder until live)
                                 Send to subscribers
                                 Insert to newsletter_runs
  ↓
Converge Outputs  (append, 3 inputs)
  ↓
Webhook Response  (JSON summary)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | n8n (self-hosted) |
| Patent data | USPTO PatentsView API — free, no auth required |
| LLM | Claude Sonnet (`claude-sonnet-4-6`) — 7 parallel chains |
| Storage | Supabase (PostgreSQL + JSONB) |
| Email | SendGrid or n8n native SMTP node |

---

## Prerequisites

- Node.js 18+
- n8n running locally or self-hosted
- Supabase project (free tier is sufficient)
- Anthropic API key — [console.anthropic.com](https://console.anthropic.com)
- SendGrid account or any SMTP credentials

---

## Supabase Setup

Open the Supabase SQL editor and run all four statements:

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

create table newsletter_subscribers (
  id uuid default gen_random_uuid() primary key,
  created_at timestamptz default now(),
  email text unique not null
);
```

Disable RLS on all four tables:

```sql
alter table patent_runs disable row level security;
alter table newsletter_runs disable row level security;
alter table error_log disable row level security;
alter table newsletter_subscribers disable row level security;
```

---

## Credentials

**Find and replace in `workflow.json` before importing:**

| Placeholder | Where to get it |
|---|---|
| `YOUR_SUPABASE_URL` | Supabase → Project Settings → API |
| `YOUR_SUPABASE_ANON_KEY` | Supabase → Project Settings → API (anon key) |
| `YOUR_MYCROFT_ORCHESTRATION_ENDPOINT` | Replace with `https://httpbin.org/post` for now |
| `YOUR_AGENT_SECRET` | Replace with any placeholder string for now |

**Set as environment variable before starting n8n:**

```bash
export PIPELINE_SECRET=your-long-random-string
npx n8n
```

**Create in the n8n UI after importing:**

- **Anthropic API** credential — paste your key, bind to all 7 Anthropic Model nodes (1–6 + Newsletter)
- **SMTP or SendGrid** credential — bind to the Send Email node

`YOUR_ANTHROPIC_CREDENTIAL_NAME`, `YOUR_ANTHROPIC_CREDENTIAL_ID`, `YOUR_SMTP_CREDENTIAL_NAME`, and `YOUR_SMTP_CREDENTIAL_ID` are all bound in the n8n UI after import — n8n assigns real IDs when you save each credential. Do not find-replace these in the file.

---

## Import & Activate

1. Find-and-replace all placeholders in `workflow.json` as listed above
2. n8n → **Workflows → Import from File** → select `workflow.json`
3. Create Anthropic API credential → bind to all 7 Anthropic Model nodes
4. Create SMTP/SendGrid credential → bind to Send Email node
5. Replace the 5 assignee ID placeholders in the **Fetch Patent Data** code node (see below)
6. Add at least one subscriber: `insert into newsletter_subscribers (email) values ('your@email.com');`
7. Save — leave inactive until you've done a manual test run

---

## PatentsView Assignee IDs

The workflow ships with placeholder strings (`nvidia-assignee-id`, `amd-assignee-id`, etc.). Without real IDs every patent fetch returns 0 results.

1. Go to [patentsview.org/query/builder](https://patentsview.org/query/builder)
2. Search each company name
3. Copy the `assignee_id` from the results
4. Open the **Fetch Patent Data** Code node in n8n
5. Replace the 5 placeholders with real values

The workflow falls back to alias string matching if the primary ID query returns zero, but that path is noisier.

---

## First Run

```bash
curl -H "X-Pipeline-Secret: $PIPELINE_SECRET" \
  http://localhost:5678/webhook/run-patent-pipeline
```

Takes 60–120 seconds. Check Supabase → `patent_runs` for a new row. If `total_patents_analyzed` is 0, the assignee IDs are still placeholders.

---

## Adding Newsletter Subscribers

```sql
insert into newsletter_subscribers (email) values
  ('researcher1@example.com'),
  ('researcher2@example.com');
```

The newsletter branch is gated on `totalPatentsAnalyzed >= 200` — below that threshold the run is too thin for a useful briefing and the branch is skipped, logging `NEWSLETTER_SKIPPED` to `error_log`.

---

## Sample Output

```json
{
  "status": "success",
  "runId": "f3a1c8e2-7b4d-4f9a-bc2e-1d3e5f7a9b0c",
  "date": "2026-06-15",
  "totalPatentsAnalyzed": 312,
  "signals": [
    {
      "company": "NVIDIA",
      "signalType": "PATENT_VELOCITY",
      "velocityScore": 87,
      "trend": "ACCELERATING",
      "noveltyScore": 74,
      "newConcepts": ["speculative decoding", "world model training"],
      "teamExpansionSignal": "EXPANDING",
      "newInventorCount": 14,
      "intent": "Expansive",
      "breakthroughScore": 68,
      "breakthroughPatents": ["US20260183421", "US20260191038"],
      "investmentSignal": "ACCUMULATE",
      "signalExpiresAt": "2026-09-13T06:00:00.000Z",
      "confidence": 0.84
    },
    {
      "company": "Intel",
      "signalType": "PATENT_VELOCITY",
      "velocityScore": 31,
      "trend": "DECELERATING",
      "noveltyScore": 22,
      "newConcepts": [],
      "teamExpansionSignal": "CONTRACTING",
      "newInventorCount": 2,
      "intent": "Defensive",
      "breakthroughScore": 18,
      "breakthroughPatents": [],
      "investmentSignal": "REDUCE",
      "signalExpiresAt": "2026-09-13T06:00:00.000Z",
      "confidence": 0.79
    },
    {
      "company": "Google",
      "signalType": "PATENT_VELOCITY",
      "velocityScore": 91,
      "trend": "ACCELERATING",
      "noveltyScore": 88,
      "newConcepts": ["mixture-of-experts routing", "in-context RL"],
      "teamExpansionSignal": "EXPANDING",
      "newInventorCount": 22,
      "intent": "Foundational",
      "breakthroughScore": 81,
      "breakthroughPatents": ["US20260174892"],
      "investmentSignal": "ACCUMULATE",
      "signalExpiresAt": "2026-09-13T06:00:00.000Z",
      "confidence": 0.91
    }
  ],
  "convergence": {
    "convergenceTopics": [
      "transformer inference optimization",
      "on-device neural processing"
    ],
    "divergenceTopics": [
      "NVIDIA: world model simulation",
      "Google: in-context learning primitives"
    ],
    "strategicInsight": "All five companies are converging on inference
      efficiency IP while NVIDIA and Google are staking out divergent
      bets in simulation and in-context learning respectively."
  },
  "newsletterStatus": "sent",
  "newsletterSentTo": 3,
  "processingMs": 84320
}
```

---

## Known Limitations

1. **USPTO shows published patents, not filed.** PatentsView exposes the grant/publication date, which lags the filing date by roughly 18 months. Treat velocity as a medium-term trend signal, not real-time news.
2. **Assignee IDs are placeholders.** Real PatentsView IDs must be substituted before the first run — see above.
3. **Company name normalization is incomplete for subsidiaries.** Aliases are hardcoded (e.g. `Alphabet`, `DeepMind`, `Google DeepMind Technologies Limited`). Acquisitions and historical assignee strings outside that list are missed.
4. **CPC scope may exclude relevant subcodes.** Currently `G06N` and `H01L` only. Neighboring areas (`G06F`, `G11C`, parts of `H03K`) are out of scope.
5. **Concept novelty requires 2+ runs to be meaningful.** The first run has empty `previousConcepts` so Claude scores by within-batch dominance. Trust the signal from the second run onward.
6. **Signal Aggregator field-matching fails silently on unexpected Claude output shapes.** If a Claude response drifts schema, that signal defaults to empty and a row is written to `error_log` with `error_type: UNRECOGNISED_SHAPE`.
7. **Strategic intent stability across runs is unvalidated.** Single-run intent classifications should be treated with caution — trust patterns that persist across multiple runs.
8. **Investment signal is experimental and is not financial advice.** The `ACCUMULATE / WATCH / HOLD / REDUCE` mapping is a deterministic rule derived from the other six signals. It is not a recommendation.
9. **Newsletter is skipped when `totalPatentsAnalyzed < 200`.** The skip is logged to `error_log` with `error_type: NEWSLETTER_SKIPPED`.
10. **Orchestration endpoint is a placeholder.** Replace `YOUR_MYCROFT_ORCHESTRATION_ENDPOINT` with `https://httpbin.org/post` for now — the workflow logs non-2xx responses but does not fail.
11. **PatentsView fetch uses page 1 / 100 results per alias only.** Companies with more than ~100 matching patents in the date window will be truncated.

---

## Project Structure

```
patent-filing-velocity-tracker/
├── workflow.json
├── setup.sql
└── README.md
```

---

## Author

**Sahiti Nallamolu**

- LinkedIn: [linkedin.com/in/sahitinallamolu](https://www.linkedin.com/in/sahitinallamolu/)
- Humanitarians AI Fellow