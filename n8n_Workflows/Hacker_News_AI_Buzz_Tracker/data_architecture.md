# Hacker News AI Buzz Tracker: Data Architecture

> Companion to `proposal.md` and `system_architecture.md`. This document specifies the **data architecture** for Phase 1: the persistent schema (Supabase Postgres), the watchlist composition (the normalization universe), the trailing-window specification, and the consolidated resolution of the four flags raised in the proposal review (`/v1`). Where the system architecture describes how data *flows*, this document describes how data is *shaped, stored, and governed*.

## 1. Data domains

The system has four logical data domains:

1. **Configuration** — the watchlist and run-level parameters (trailing window, thresholds). Versioned, human-owned, source-controlled.
2. **Raw collection** — Hacker News story hits per entity per run. Transient; not persisted beyond the scoring step (only derived aggregates are stored).
3. **Derived state** — per-entity Buzz Scores, components, velocity, and confidence flags, persisted per run. This is the historical series that velocity depends on.
4. **Outputs** — the human digest (rendered, not stored as a row) and fired alerts (persisted for audit and de-duplication).

## 2. Trailing window specification (FLAG-3, resolved)

`TRAILING_WINDOW_DAYS = 14`, exposed as a single run-level config value emitted by the Watchlist node and stored on each run header for provenance.

- **Collection bound:** each entity query filters `created_at_i > (run_epoch − 14·86400)`.
- **Baseline definition:** the *trailing average* for an entity is the mean Buzz Score over the entity's complete runs within the last 14 calendar days (not the average of raw story counts — the average is computed over the derived daily score series).
- **Cold-start bound:** velocity is unavailable on run 1; partially informative from run 2–3; the trailing average is considered fully populated once ≥ 14 daily complete runs exist. The acceleration scoring component is forced to 0 until at least one prior complete run exists.
- **Rationale (owned opinion):** 7 days yields an unstable baseline (a quiet weekend distorts it) and an unreliable cold start; 30 days dilutes the 3-day surges the signal exists to catch. 14 days balances baseline stability against breakout sensitivity. Revisited against Phase 1 data alongside score weights and thresholds; changing it is a config edit, not a code change.

## 3. Watchlist composition (FLAG-1, resolved)

The watchlist **is** the normalization universe: cross-entity log normalization is computed over exactly these entities, so the set is frozen within a phase and versioned across phases. Query-term ambiguity is the highest-risk failure mode, so terms are deliberately specific and qualified.

**Watchlist v1 — 13 entities (frozen for Phase 1):**

| `entity_id` | Display name | Ticker | Investable | Query terms (OR-matched) | Aliases → roll up | Breakout threshold |
| --- | --- | --- | --- | --- | --- | --- |
| `nvidia` | NVIDIA | NVDA | yes | `NVIDIA`, `CUDA`, `Blackwell GPU`, `H100`, `GB200` | NVIDIA Corp | default |
| `microsoft_ai` | Microsoft AI | MSFT | yes | `Microsoft Copilot`, `Azure OpenAI`, `Microsoft AI` | Copilot, Azure AI | default |
| `google_deepmind` | Alphabet / Google DeepMind | GOOGL | yes | `Google DeepMind`, `Gemini model`, `Google AI`, `Vertex AI` | DeepMind, Gemini | default |
| `meta_ai` | Meta AI | META | yes | `Meta AI`, `Llama model`, `Llama 3`, `Llama 4`, `PyTorch` | Llama, FAIR | default |
| `amazon_ai` | Amazon AI | AMZN | yes | `Amazon Bedrock`, `AWS Trainium`, `Amazon Q`, `SageMaker` | Bedrock, AWS AI | default |
| `amd` | AMD | AMD | yes | `AMD MI300`, `AMD Instinct`, `ROCm`, `AMD AI` | Instinct, ROCm | default |
| `broadcom` | Broadcom | AVGO | yes | `Broadcom AI`, `Broadcom custom silicon`, `Broadcom accelerator` | — | default |
| `oracle_ai` | Oracle Cloud AI | ORCL | yes | `Oracle Cloud Infrastructure AI`, `OCI GPU`, `Oracle AI` | OCI | default |
| `palantir` | Palantir | PLTR | yes | `Palantir AIP`, `Palantir Foundry`, `Palantir AI` | AIP, Foundry | default |
| `coreweave` | CoreWeave | CRWV | yes | `CoreWeave`, `CoreWeave GPU cloud` | — | default |
| `openai` | OpenAI | — | no (private) | `OpenAI`, `ChatGPT`, `GPT-4`, `GPT-5`, `o1 model`, `Sora` | ChatGPT, GPT, Sora | default |
| `anthropic` | Anthropic | — | no (private) | `Anthropic`, `Claude model`, `Claude Code`, `Claude API` | Claude | default |
| `mistral` | Mistral AI | — | no (private) | `Mistral AI`, `Mistral model`, `Mixtral`, `Le Chat` | Mixtral | default |

- **`entity_id`** is the stable join key across all tables and the coordination-layer signal; display names and query terms may be revised in v2, but `entity_id` is immutable.
- **Governance:** static within Phase 1; additions/removals only at a version boundary (v1 → v2), which creates a normalization discontinuity (historical scores valid within a version, not compared across the boundary). Owner: project maintainer (`mali.om@northeastern.edu`).
- **`investable=false`** entities (private labs) are included for context and clearly flagged as non-investable in every output.

### 3.1 Watchlist record (configuration schema)

The Watchlist Set node emits one item per entity matching this shape (also the canonical source-controlled watchlist file format):

```json
{
  "entity_id": "nvidia",
  "display_name": "NVIDIA",
  "ticker": "NVDA",
  "investable": true,
  "query_terms": ["NVIDIA", "CUDA", "Blackwell GPU", "H100", "GB200"],
  "aliases": ["NVIDIA Corp"],
  "breakout_threshold": { "pct": 0.40, "min_score": 50, "abs_jump": 25 }
}
```

`breakout_threshold` defaults to the global provisional values (§5) and may be overridden per entity without code change.

## 4. Persistent schema (Supabase Postgres)

Three tables. The watchlist itself lives in source control / the Set node, not the database, but its version is stamped on every run for provenance.

### 4.1 `hn_buzz_runs` — run header (one row per daily run)

| Column | Type | Notes |
| --- | --- | --- |
| `run_id` | `uuid` PK | Generated per run. |
| `run_date` | `date` UNIQUE | UTC date; unique → re-running a day upserts, never duplicates a baseline. |
| `run_ts` | `timestamptz` | Execution start time (UTC). |
| `status` | `text` | `complete` \| `incomplete`. Only `complete` runs are eligible as a velocity baseline. |
| `watchlist_version` | `text` | e.g. `v1`. Stamps the normalization universe. |
| `trailing_window_days` | `int` | `14` in Phase 1; stored for provenance. |
| `entity_count` | `int` | Entities scored this run. |
| `cold_start` | `bool` | True while acceleration is forced to 0 (no prior complete run). |
| `created_at` | `timestamptz` default now() | |

### 4.2 `hn_buzz_entity_scores` — per-entity leaderboard (N rows per run)

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `bigint` PK | |
| `run_id` | `uuid` FK → `hn_buzz_runs` | |
| `entity_id` | `text` | Join key to the watchlist. |
| `ticker` | `text` null | Null for private entities. |
| `investable` | `bool` | |
| `story_count` | `int` | Real `0` allowed (never null). |
| `points_total` | `int` | Sum of story points. |
| `comments_total` | `int` | Sum of comment counts. |
| `front_page_count` | `int` | Stories ≥ points threshold. |
| `comp_volume` | `int` | Component, capped 30. |
| `comp_engagement` | `int` | Component, capped 30. |
| `comp_front_page` | `int` | Component, capped 20. |
| `comp_acceleration` | `int` | Component, capped 20; `0` on cold start. |
| `buzz_score` | `int` | 0–100 (sum of components, normalized). |
| `prev_buzz_score` | `int` null | From prior complete run. |
| `trailing_avg_score` | `numeric` null | 14-day mean of complete-run scores. |
| `velocity_pct` | `numeric` null | `(buzz_score − trailing_avg)/trailing_avg`. |
| `velocity_abs` | `int` null | `buzz_score − prev_buzz_score`. |
| `confidence` | `text` | `normal` \| `low` (sub-floor) \| `cold_start`. |
| `breakout` | `bool` | |
| `top_story` | `jsonb` | `{title, url, points, object_id}`. |

Index: `(entity_id, run_id)` and `(run_id)` for the leaderboard read; a covering index on `(entity_id, run_date)` (via join) supports the 14-day history query.

### 4.3 `hn_buzz_alerts` — fired alerts (audit + de-dup)

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `bigint` PK | |
| `run_id` | `uuid` FK | |
| `entity_id` | `text` null | Null for operational/pipeline alerts. |
| `alert_type` | `text` | `breakout` \| `pipeline_failure`. |
| `reason` | `text` | e.g. `pct>=0.40 && score>=50`, `abs_jump>=25`, or failure detail. |
| `payload` | `jsonb` | Score/velocity snapshot at fire time. |
| `sent_at` | `timestamptz` | |

## 5. Breakout thresholds (FLAG-2, resolved — provisional)

Stored per entity in `breakout_threshold` (§3.1); defaults are global and provisional. An entity fires a **breakout** when, in the same run:

- **(A) acceleration rule:** `velocity_pct ≥ 0.40` **AND** `buzz_score ≥ 50`, OR
- **(B) spike tripwire:** `velocity_abs ≥ 25` (regardless of A).

Constraints:

- **Confidence gate:** entities with `confidence ∈ {low, cold_start}` are **excluded** from breakout alerting until they clear the activity floor (≥ 3 stories in the window) and have a prior complete run.
- **Provisional status:** `0.40 / 50 / 25` are heuristics, set now for the discipline of a defined, testable rule, held fixed through Phase 1 for comparability, and recalibrated against accumulated data before Phase 3. They are expected to be wrong on first pass.

## 6. Scoring data rules

- **Buzz Score** ∈ `[0, 100]`, integer, deterministic given stored history + HN data. Components capped at 30 / 30 / 20 / 20.
- **Log normalization** across the watchlist universe so a few viral stories do not dominate; applied to volume and engagement.
- **Sparse entities** (`story_count < 3`): scored against an absolute floor instead of the cross-entity log scale; flagged `confidence="low"`.
- **Cold start** (no prior complete run): `comp_acceleration = 0` uniformly for all entities; flagged `confidence="cold_start"` and `run.cold_start = true`.
- **Zero hits:** stored as real `0`, yielding a floored low-confidence score — never null, never skipped.

## 7. Email delivery data (FLAG-4, resolved)

Delivery configuration (transport, not stored in Postgres):

- **Provider/transport:** SendGrid SMTP, `smtp.sendgrid.net`, port `587`, STARTTLS.
- **Credentials:** n8n SMTP credential — username `apikey`, password = SendGrid API key scoped to mail-send only; key held as an environment-level secret, never inline in workflow JSON.
- **From:** `buzz-tracker@<project-domain>` (verified sender; SendGrid single-sender verified address as setup fallback).
- **To (Phase 1):** `mali.om@northeastern.edu`.
- **Subject prefixes:** `[HN Buzz]` (digest) vs `[HN Buzz ALERT]` (breakout + pipeline failure) so they are filterable.
- **Fallback:** Gmail SMTP + app password for the single Phase 1 recipient if SendGrid sender verification is incomplete at build time.
- **Free-tier headroom:** 100 emails/day comfortably covers one daily digest plus occasional alerts.

## 8. Machine-ingestible signal (data contract)

The Mycroft coordination layer consumes the latest **complete** run directly from Postgres (Phase 1). Canonical shape:

```json
{
  "run_id": "…",
  "run_date": "2026-06-12",
  "run_ts": "2026-06-12T08:00:00Z",
  "watchlist_version": "v1",
  "trailing_window_days": 14,
  "cold_start": false,
  "leaderboard": [
    {
      "entity_id": "nvidia", "ticker": "NVDA", "investable": true,
      "buzz_score": 65, "velocity_pct": 0.578, "velocity_abs": 17,
      "confidence": "normal", "breakout": true,
      "top_story": { "title": "…", "url": "https://…" }
    }
  ]
}
```

The HTML email is for humans only and is never an ingestion path. A pull HTTP endpoint serving this same shape is a later-phase deliverable; in Phase 1 the stored snapshot is the interface.

## 9. Flag resolution summary

| Flag | Topic | Resolution | Location |
| --- | --- | --- | --- |
| FLAG-1 | Watchlist composition | 13 entities (10 ticker + 3 private), specific query terms, aliases, `entity_id` keys; v1 frozen for Phase 1. | §3, §3.1 |
| FLAG-2 | Breakout thresholds | Provisional `pct ≥ 0.40 & score ≥ 50`, OR `abs_jump ≥ 25`; confidence-gated; per-entity overridable; recalibrated post-Phase 1. | §5 |
| FLAG-3 | Trailing window | `14 days`, parameterized (`TRAILING_WINDOW_DAYS`), owned rationale; stamped on each run. | §2 |
| FLAG-4 | Email delivery | SendGrid SMTP `:587` STARTTLS, credentialed API key, verified from-address, maintainer to-address, Gmail fallback. | §7 |
