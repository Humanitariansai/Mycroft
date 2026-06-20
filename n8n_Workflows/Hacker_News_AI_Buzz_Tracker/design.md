# Hacker News AI Buzz Tracker — Design Document

> Week 1 design spec: data model, Buzz Score formula, HN Algolia API reference, and the planned
> workflow architecture. This is the design contract that Weeks 2–4 build against. No code yet.

**Author:** Om Mali
**Status:** Draft (Week 1) — design only

---

## 1. Overview

The agent tracks a configurable watchlist of AI entities on Hacker News, computes a deterministic
**Buzz Score (0–100)** per entity over a trailing window, compares it to the previous run to get
**buzz velocity**, stores the snapshot, and emails a ranked digest. It reads from one free,
no-key source (the HN Algolia Search API) and adds an LLM narrative layer in a later month.

The signal measures **attention, not direction** — heavy discussion of an outage and a celebrated
launch both score high. Distinguishing them is the LLM reception-tone layer's job (Month 2).

---

## 2. Data source — HN Algolia Search API

Free, no key, no signup. Base endpoint:

```
https://hn.algolia.com/api/v1/search_by_date?query={term}&tags=story&numericFilters=created_at_i>{since_unix}
```

### Key parameters

| Param | Purpose | Notes |
|-------|---------|-------|
| `query` | search term(s) | matched against title + url + text |
| `tags=story` | restrict to stories | excludes comments, polls, jobs |
| `numericFilters=created_at_i>{unix}` | trailing-window filter | `since_unix` = now − windowHours |
| `page` | pagination, 0-indexed | response reports `nbPages`, `nbHits` |
| `hitsPerPage` | results per page | default 20, request up to 100 wis not gauranteed |

`search_by_date` sorts newest-first (good for a trailing window). `search` (relevance-sorted) is
the alternative but less suited to time-bounded volume counting.

### Response shape (fields we use)

```jsonc
{
  "hits": [
    {
      "title": "OpenAI releases ...",
      "url": "https://...",
      "points": 412,
      "num_comments": 233,
      "created_at_i": 1749500000,   // unix seconds
      "objectID": "40123456"         // dedupe key + permalink id
    }
  ],
  "nbHits": 57,
  "nbPages": 3,
  "page": 0,
  "hitsPerPage": 20
}
```

Story permalink: `https://news.ycombinator.com/item?id={objectID}`.

### Computing the trailing window (PowerShell)

```powershell
$sinceUnix = [DateTimeOffset]::UtcNow.AddHours(-24).ToUnixTimeSeconds()
```

### API findings (Week 1 exploration — 2026-06-09)

Verified by hand against a live trailing-window query.

**Request**
```
https://hn.algolia.com/api/v1/search_by_date?query=Apple%20Intelligence&tags=story&numericFilters=created_at_i>1780443734
```

**Result:** HTTP 200, `nbHits: 6`, `nbPages: 1`, `hitsPerPage: 20`, `page: 0`,
`processingTimeMS: 10`. Trimmed top hit:

```jsonc
{
  "title": "Apple unveils innovative features and intelligence experiences across services",
  "url": "https://www.apple.com/newsroom/2026/06/apple-unveils-...",
  "author": "soheilpro",
  "points": 1,
  "num_comments": 0,
  "created_at": "2026-06-09T13:12:11Z",
  "created_at_i": 1781010731,
  "objectID": "48460690",
  "story_id": 48460690
}
```

**Confirmed**
- All fields the score depends on are present: `title`, `url`, `points`, `num_comments`,
  `created_at_i`, `objectID`. `created_at` (ISO string) and `author` also come for free.
- `tags=story` is echoed in `params`; results are stories only.
- The `numericFilters=created_at_i>{unix}` trailing-window filter works — every hit's
  `created_at_i` is greater than the supplied bound.
- Top-level `nbHits` (here 6) is the window count we use for the Volume component; `nbPages` tells
  us whether to paginate (here 1, so no pagination needed).
- `hitsPerPage` defaults to **20**. Each hit carries a `_highlightResult` block (matched-word
  highlighting with `<em>` tags) — **noise we ignore**; we read only the plain fields above.

**Implications for the build**
- Multi-term entities (e.g. "Apple Intelligence") work as a phrase query and matched on both title
  and url. Generic terms will pull adjacent stories — query-term precision matters (see Risks §7).
- Low-engagement reality check: even a relevant breaking story can sit at `points: 1`,
  `num_comments: 0` shortly after posting. Scoring must treat thin/early windows as a valid low
  baseline, not an error.
- For windows with `nbPages > 1`, page through with `page` until `page >= nbPages` (Week 2).

> Not yet exercised: explicit rate-limit / 429 behavior under rapid calls (the API is documented as
> generous and no key is required). Revisit during the Week 9 historical backfill when call volume
> is high.

---

## 3. Watchlist data model

Stored in `watchlist.json`, one object per entity:

```jsonc
{
  "entity": "NVIDIA",            // canonical display name + dedupe rollup key
  "ticker": "NVDA",             // null for private comparables
  "queryTerms": ["NVIDIA", "Nvidia", "CUDA"],  // OR'd / queried per term
  "frontPagePoints": 100,        // points threshold for "front page impact"
  "breakoutThreshold": 70        // Buzz Score that fires a breakout alert
}
```

Aliases (a company and its flagship model, e.g. Meta + Llama, Google + Gemini) roll up to **one**
entity so attention isn't split. Multi-term entities query each term and merge hits, deduping by
`objectID`.

### Watchlist v1 (10–15 entities)

| Entity | Ticker | Sample query terms |
|--------|--------|--------------------|
| NVIDIA | NVDA | NVIDIA, CUDA |
| Microsoft / OpenAI | MSFT | OpenAI, ChatGPT, GPT |
| Google / Gemini | GOOGL | Gemini, DeepMind |
| Meta / Llama | META | Llama, Meta AI |
| AMD | AMD | AMD, ROCm |
| Palantir | PLTR | Palantir |
| Anthropic | — | Anthropic, Claude |
| Mistral | — | Mistral |

(Final v1 list lives in `watchlist.json`; expand to 10–15 there.)

---

## 4. Buzz Score model (deterministic, 0–100)

Four additive components. The LLM adds only the qualitative layer later; the score itself is fully
deterministic and reproducible.

| Component | Range | Input | Intent |
|-----------|-------|-------|--------|
| **Volume** | 0–30 | story count in window | how much is being posted |
| **Engagement** | 0–30 | total points + comments | how hard people are reacting |
| **Front-page impact** | 0–20 | # stories ≥ `frontPagePoints` | did anything actually break out |
| **Acceleration** | 0–20 | growth vs. trailing average | is attention rising |

```
BuzzScore = Volume + Engagement + FrontPage + Acceleration   // clamped to [0, 100]
```

### Normalization (log scale)

Raw counts are heavy-tailed — a single viral story can dominate. Each component is normalized on a
**log scale** across entities so a few front-page hits don't saturate the score. Sketch:

```
volumeScore     = 30 * clamp( log1p(storyCount)      / log1p(VOLUME_REF),     0, 1 )
engagementScore = 30 * clamp( log1p(points+comments) / log1p(ENGAGEMENT_REF), 0, 1 )
frontPageScore  = 20 * clamp( frontPageCount         / FRONTPAGE_REF,         0, 1 )
accelScore      = 20 * clamp( (current - trailingAvg)/ max(trailingAvg, 1),   0, 1 )
```

Reference constants (`VOLUME_REF`, `ENGAGEMENT_REF`, `FRONTPAGE_REF`) are calibration knobs — the
exact values and the full golden-fixture validation are the **Week 3** deliverable (`scoring_logic.md`).
This doc fixes the *shape* of the formula, not the final constants.

### Buzz Velocity (Week 4)

```
velocity = currentScore - previousScore       // simple delta vs. last run
accel    = current rawVolume vs. trailing avg  // feeds the Acceleration component above
```

First run has no prior snapshot → velocity baselines to **0** (not an error). Cold-start velocity
stays conservative until enough runs accumulate (historical backfill in Month 3 is the fix).

### Edge cases the scoring must handle

- Zero-hit entity → all components 0, Buzz Score 0 (valid, not an error).
- Empty / malformed API response → degrade gracefully, skip entity, keep the run alive.
- Missing prior snapshot → velocity = 0.
- Missing LLM key (later months) → fall back to deterministic score + digest.

---

## 5. Storage schema (planned — table created Week 4)

Supabase Postgres. Documented now; not provisioned in Week 1.

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

- `leaderboard` — ranked entities with scores, velocity, top story.
- `narratives` — per-entity narrative/theme/tone (populated once the LLM layer lands).
- `raw_metrics` — the underlying volume/points/comments/front-page counts for auditing scores.

---

## 6. Workflow architecture (target end state)

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

### Build phasing (which weeks touch which nodes)

| Weeks | Nodes added |
|-------|-------------|
| **2** | Schedule Trigger, Watchlist Set, Split In Batches, HTTP Request, parse/dedupe/normalize Code |
| **3** | Buzz Score components in the Code node, log normalization, golden fixtures |
| **4** | Postgres read + insert, velocity Code node, simple ranked email digest |
| **5+** | LLM narrative node, richer HTML digest, alerts, dashboard webhook |

---

## 7. Known risks (from proposal.md)

- **Name ambiguity** — generic query terms pull unrelated stories; careful `queryTerms` + filtering
  is the main noise control.
- **Thin/empty windows** — small/private entities give jumpy scores; treat zero hits as a baseline.
- **Cold-start velocity** — needs history; early numbers are conservative until backfill (Month 3).
- **Score calibration** — weights and the points threshold are judgment calls; tune against real
  data before trusting the numbers.
- **Buzz ≠ direction** — high score = attention, not good news; reception-tone layer addresses this.
- **Single-source dependency** — if the HN API rate-limits or changes shape, collection stops;
  wrap requests in basic error handling.
