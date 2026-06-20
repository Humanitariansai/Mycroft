# Hacker News AI Buzz Tracker: System Architecture

> Companion to `proposal.md`. This document specifies the **system architecture** for Phase 1: the component decomposition, the data flow between components, the interface contracts at each boundary, and the technology decisions with their rationale. The data schema and watchlist universe are specified separately in `data_architecture.md`.

## 1. Scope and architectural goals

Phase 1 delivers a **single n8n workflow** that runs once daily, end to end, with no LLM and no dashboard. The architecture is deliberately constrained to one orchestrator (n8n), one external read source (Hacker News Search API), one persistent store (Supabase Postgres), and one delivery channel (SMTP email). Every component is either a managed free tier or a no-key public API.

The architecture optimizes for four properties, in priority order:

1. **Determinism** — given the same stored history and the same Hacker News data, a run produces the same Buzz Scores. No randomness, no model calls in the scoring path.
2. **Graceful degradation** — a rate limit, an empty response, or a missing prior snapshot degrades to a defined, conservative output rather than failing the run.
3. **Separation of human and machine outputs** — the human digest (HTML email) and the machine signal (structured JSON in Postgres) are distinct artifacts produced from the same run.
4. **Reconfigurability without code change** — the watchlist, trailing window, and breakout thresholds are parameters, not hard-coded constants.

## 2. Component diagram

```
                          ┌──────────────────────────────────────────────────┐
                          │                  n8n Workflow                      │
                          │             (single daily execution)               │
                          │                                                    │
   ┌────────────┐  fires  │  ┌────────────┐    ┌────────────────────────────┐ │
   │  Schedule  │────────►│  │  Watchlist  │    │   Loop (Split In Batches)  │ │
   │  Trigger   │  daily  │  │  (Set node) │───►│   one iteration / entity   │ │
   └────────────┘         │  └────────────┘    └─────────────┬──────────────┘ │
                          │                                  │ per entity      │
                          │                                  ▼                 │
   ┌────────────────┐     │                       ┌────────────────────┐       │
   │  Hacker News   │◄────┼───────────────────────│   HTTP Request     │       │
   │  Search API    │ GET │   stories (JSON)       │   (Algolia HN)     │       │
   │  (Algolia)     │────►│                        └─────────┬──────────┘       │
   └────────────────┘     │                                  ▼                  │
                          │                       ┌────────────────────┐        │
                          │                       │ Aggregate & Score  │        │
                          │                       │   (Code node)      │        │
                          │                       └─────────┬──────────┘        │
                          │            (after loop completes)│ scored entities  │
                          │                                  ▼                  │
   ┌────────────────┐     │   read prior run      ┌────────────────────┐        │
   │   Supabase     │◄────┼───────────────────────│ Read Prev Snapshot │        │
   │   Postgres     │────►│   prior leaderboard    │   (Postgres)       │        │
   │                │     │                        └─────────┬──────────┘        │
   │  hn_buzz_runs  │     │                                  ▼                   │
   │  hn_buzz_      │     │                       ┌────────────────────┐         │
   │   entity_scores│     │                       │  Compute Velocity  │         │
   │  hn_buzz_alerts│     │                       │   (Code node)      │         │
   └────────────────┘     │                       └─────────┬──────────┘         │
            ▲             │                                  ▼                   │
            │  write run  │                       ┌────────────────────┐         │
            └─────────────┼───────────────────────│  Store Snapshot    │         │
                          │                        │   (Postgres)       │        │
                          │                        └─────────┬──────────┘        │
                          │                                  ▼                   │
                          │                       ┌────────────────────┐         │
                          │                       │ Build Digest/Alert │         │
                          │                       │   (Code node)      │         │
                          │                       └─────────┬──────────┘         │
                          │                                  ▼                   │
   ┌────────────────┐     │   send HTML email     ┌────────────────────┐         │
   │  SendGrid SMTP │◄────┼───────────────────────│  Send Email (SMTP) │         │
   │  smtp.sendgrid │     │                        └────────────────────┘        │
   │  .net:587      │     │                                                       │
   └───────┬────────┘     └───────────────────────────────────────────────────--┘
           │ deliver
           ▼
   ┌────────────────┐                              ┌────────────────────────────┐
   │  Maintainer    │                              │  Mycroft Coordination Layer │
   │  inbox (digest │                              │  (consumes JSON signal from │
   │  + alerts)     │                              │   stored snapshot — Phase 1) │
   └────────────────┘                              └────────────────────────────┘
```

The error-handling path is orthogonal to the main flow: the HTTP Request and the two Postgres write/read steps are wrapped so failures route to a **Pipeline-Failure Alert** (a maintainer email with the `[HN Buzz ALERT]` prefix) rather than aborting silently. This alert is distinct from the entity breakout alert.

## 3. Components

| # | Component | n8n node type | Responsibility |
| --- | --- | --- | --- |
| C1 | Schedule Trigger | Schedule Trigger | Fire the workflow once per day at a fixed UTC time. |
| C2 | Watchlist | Set | Emit the v1 watchlist (13 entities, query terms, ticker, per-entity breakout threshold) plus run-level config (`TRAILING_WINDOW_DAYS=14`). |
| C3 | Loop | Split In Batches | Iterate the watchlist so each entity is collected independently; isolates a per-entity failure to that entity. |
| C4 | Collector | HTTP Request | Query the Hacker News Search API for one entity's query terms over the trailing window. |
| C5 | Aggregate & Score | Code | Parse hits, dedupe by `objectID`, normalize aliases to one entity, compute the four scoring components and the 0–100 Buzz Score. |
| C6 | Read Prev Snapshot | Postgres (select) | Load the most recent *complete* prior run and the trailing-window per-entity history. |
| C7 | Compute Velocity | Code | Compute change vs. trailing 14-day average; evaluate breakout rules; mark low-confidence entities. |
| C8 | Store Snapshot | Postgres (insert) | Persist the run, the per-entity leaderboard, and fired alerts. |
| C9 | Build Digest/Alert | Code | Render the ranked HTML digest and assemble breakout alert payloads. |
| C10 | Send Email | Send Email (SMTP) | Deliver the digest and any alerts via SendGrid SMTP. |

## 4. Data flow

A single run proceeds as a linear pipeline with one fan-out (the loop) and one fan-in (scoring runs per entity, velocity onward runs once over the full set):

1. **Trigger → Watchlist.** C1 fires; C2 emits 13 entity items + config.
2. **Watchlist → Collector (per entity).** C3 hands each entity to C4. C4 issues a `search_by_date` query bounded by `created_at_i > now − 14d`.
3. **Collector → Score (per entity).** C5 receives raw hits, dedupes, normalizes, and produces one **scored entity record** per watchlist entity.
4. **Fan-in → Read history.** After the loop completes, C6 reads the prior complete snapshot and the 14-day history for all entities in one query.
5. **Score + history → Velocity.** C7 joins current scores with history, computes velocity and acceleration, applies breakout rules, and sets confidence flags.
6. **Velocity → Store.** C8 writes the run header, the per-entity rows, and any alert rows transactionally.
7. **Store → Digest.** C9 builds the human HTML digest (ranked) and the alert payloads from the now-persisted snapshot.
8. **Digest → Email.** C10 sends the digest (`[HN Buzz]`) and, separately, any breakout alerts (`[HN Buzz ALERT]`).
9. **Machine signal.** The stored snapshot in Postgres **is** the canonical machine output; the Mycroft coordination layer reads it directly (Phase 1) — no separate emission step.

The store-before-digest ordering is deliberate: the digest and alerts are rendered from persisted data so the human email can never describe a state that was not durably recorded.

## 5. Interface contracts

### 5.1 Collector → Hacker News Search API (C4 boundary)

- **Endpoint:** `GET https://hn.algolia.com/api/v1/search_by_date`
- **Auth:** none (no key).
- **Query params:** `query=<OR-joined terms>`, `tags=story`, `numericFilters=created_at_i>{windowStartEpoch}`, `hitsPerPage=100`, paginated via `page`.
- **Response (consumed fields):** `hits[].objectID`, `hits[].title`, `hits[].url`, `hits[].points`, `hits[].num_comments`, `hits[].created_at_i`.
- **Failure modes:** HTTP 429 (rate limit) and 5xx → retry with backoff (see §6); persistent failure → the entity's collection is marked failed and the run is flagged incomplete (see §7).

### 5.2 Score node output contract (C5 → C6/C7)

One **scored entity record** per watchlist entity:

```json
{
  "entity_id": "nvidia",
  "ticker": "NVDA",
  "investable": true,
  "window_days": 14,
  "story_count": 12,
  "engagement": { "points": 940, "comments": 612 },
  "front_page_count": 3,
  "components": { "volume": 26, "engagement": 24, "front_page": 15, "acceleration": 0 },
  "buzz_score": 65,
  "confidence": "normal",          // "normal" | "low" (sub-floor) | "cold_start"
  "top_story": { "title": "...", "url": "https://...", "points": 410, "object_id": "..." }
}
```

Contract guarantees: `buzz_score` is an integer 0–100; `story_count` of 0 is a valid value (never null); `confidence="cold_start"` forces `components.acceleration=0`.

### 5.3 Velocity node output contract (C7 → C8/C9)

Extends each scored record with:

```json
{
  "prev_buzz_score": 48,
  "trailing_avg_score": 41.2,
  "velocity_pct": 0.578,           // (buzz_score - trailing_avg) / trailing_avg
  "velocity_abs": 17,              // buzz_score - prev_buzz_score
  "breakout": true,
  "breakout_reason": "pct>=0.40 && score>=50"   // or "abs_jump>=25", or null
}
```

If no prior history exists for an entity, `prev_buzz_score`, `trailing_avg_score`, and `velocity_*` are null and `breakout=false` (cold start cannot break out).

### 5.4 Store node contract (C8 → Postgres)

Writes are transactional: a run header row, N per-entity rows, and M alert rows commit together or not at all. Schema is defined in `data_architecture.md`. The run header carries `status ∈ {complete, incomplete}`; only `complete` runs are eligible as a future velocity baseline.

### 5.5 Machine signal contract (Postgres → Mycroft coordination layer)

The coordination layer consumes the latest **complete** run as JSON: `run_id`, `run_ts`, and the ranked leaderboard array of velocity records (§5.3) including `confidence` and `breakout` flags. This is a read against the stored snapshot in Phase 1; a pull HTTP endpoint is a later-phase deliverable. The email is never an ingestion path.

### 5.6 Email contract (C10 → SMTP)

- **Transport:** SendGrid SMTP, `smtp.sendgrid.net:587`, STARTTLS, username `apikey`, password = SendGrid API key (mail-send scope), stored as an n8n credential — never inline in workflow JSON.
- **Digest:** subject `[HN Buzz] Daily AI Buzz — <date>`; HTML body = ranked leaderboard. From `buzz-tracker@<project-domain>`; to `mali.om@northeastern.edu`.
- **Alert:** subject `[HN Buzz ALERT] <entity> breakout` (entity) or `[HN Buzz ALERT] pipeline failure` (operational); plain summary body.
- **Fallback:** Gmail SMTP + app password for the single Phase 1 recipient if SendGrid sender verification is incomplete at build time.

## 6. Cross-cutting concerns

- **Retries.** C4 and Postgres nodes use n8n's built-in retry-on-fail (3 attempts, exponential backoff) for transient 429/5xx/connection errors.
- **Idempotency.** A run is keyed by its UTC date; re-running the same day upserts on `run_date` rather than creating a duplicate baseline.
- **Secrets.** SendGrid API key, Supabase connection string, and any SMTP fallback credentials live in n8n credentials / environment, not in the exported workflow.
- **Time base.** All windows and run timestamps are UTC to keep the trailing-window boundary stable regardless of execution host.

## 7. Failure handling (architectural)

| Failure | Detection | Behavior |
| --- | --- | --- |
| Entity returns zero hits | `story_count == 0` | Valid data point; stored as real zero → floored low-confidence score. Not an error. |
| One entity's collection fails | C4 exhausts retries | Run marked `incomplete`; that entity excluded from this run's velocity; the prior **complete** snapshot remains the baseline. |
| No prior snapshot (cold start) | C6 returns empty | Acceleration component = 0 uniformly; `confidence="cold_start"`; surfaced in digest. |
| Storage write fails | C8 error | Pipeline-failure alert to maintainer; run not committed (no partial baseline). |
| API response shape changes | C5 schema guard | Pipeline-failure alert; run flagged incomplete. |

A partial snapshot is **never** used as the velocity baseline for the next run — this is the central invariant protecting the velocity series from corruption.

## 8. Technology decisions

| Decision | Choice | Rationale | Alternatives rejected |
| --- | --- | --- | --- |
| Orchestrator | **n8n** | Visual, node-based, free self-host; matches Mycroft's existing workflow tooling; built-in scheduling, retries, and credential store. | Cron + script (no UI, no credential mgmt); Airflow (operationally heavy for one daily DAG). |
| Data source | **HN Search API (Algolia)** | No key, free, returns points/comments/timestamps directly; the canonical HN search backend. | HN Firebase API (no full-text search); scraping (fragile, ToS risk). |
| Collection mode | **`search_by_date`** with numeric time filter | Deterministic windowing on `created_at_i`; avoids relevance-ranking nondeterminism of `search`. | `search` (relevance-ordered, less reproducible). |
| Persistence | **Supabase Postgres** | Free tier; real SQL for windowed history queries; managed, no ops; JSON columns for leaderboard payloads. | SQLite (no managed access for coordination layer); n8n static data (not queryable, size-limited). |
| Scoring | **Deterministic Code node** (no LLM) | Reproducibility is priority #1; LLM in the scoring path would break determinism. | LLM scoring (deferred to Phase 2 narrative layer, kept out of the score). |
| Email | **SendGrid SMTP** | 100/day free tier covers digest + alerts; SMTP relay drops into native node; no mail server. | SES (AWS account overhead); self-hosted SMTP (deliverability/ops burden). Gmail SMTP is the documented fallback. |
| Normalization universe | **Versioned watchlist (v1, frozen for Phase 1)** | Cross-entity log normalization requires a fixed universe for longitudinal comparability. | Dynamic watchlist (would silently reset baselines mid-series). |

## 9. Phase boundaries (what this architecture defers)

The following are explicitly **out of scope** for the Phase 1 architecture and are flagged for later phases: the free-LLM narrative/reception-tone layer, comment-level analysis, the Chart.js dashboard, the historical backfill, the signal-validation backtest (early Phase 2), and the coordination-layer **pull endpoint** (Phase 1 exposes the signal via the stored snapshot only). Score weights, the trailing-window length, and breakout thresholds are held fixed through Phase 1 and recalibrated against accumulated data afterward.
