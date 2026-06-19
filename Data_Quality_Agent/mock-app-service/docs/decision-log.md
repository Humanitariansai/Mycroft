# Decision Log

Append-only. One entry per non-obvious decision. Format borrowed from CLAUDE.md §3.5.

---

## 2026-05-21 — DuckDB for the analytics layer

Context: project-plan.md and phase-1-plan.md leave DuckDB vs Postgres open for the analytics warehouse.

Options considered:
- DuckDB via `dbt-duckdb`, sourced from Parquet files extracted from Postgres.
- Postgres-as-warehouse via `dbt-postgres`, pointed at the same Postgres that the operational app uses (different schema).

Decision: **DuckDB.**

Rationale: faster local demo, no second container, mature `dbt-duckdb` adapter. Using the operational Postgres as warehouse muddies the demo — the cross-system boundary is the whole thesis. Parquet extraction by a small Python script also mirrors what real EL tools (Fivetran, Airbyte) do in production.

Revisit if: dbt tests against DuckDB don't translate to the Postgres dialect the agent's reviewers might assume; or if a stakeholder wants a Postgres-warehouse variant for the writeup.

---

## 2026-05-21 — Native Postgres ENUM, not VARCHAR + CHECK

Context: `subscription_status` could be a `VARCHAR` with a `CHECK` constraint, or a Postgres native `ENUM`.

Options considered:
- `VARCHAR(20)` + `CHECK (status IN (...))`.
- Native `ENUM` via `CREATE TYPE subscription_status AS ENUM (...)`.

Decision: **Native ENUM.**

Rationale: makes Scenario 3's migration realistic. The native-ENUM version uses `ALTER TYPE subscription_status ADD VALUE 'paused'`, which is the exact pattern the deterministic parser will need to recognize. A `VARCHAR + CHECK` version would let the team alter the check constraint inline with the column, which is also realistic but less interesting — and the agent's parser layer will eventually need to handle the ENUM case anyway.

Revisit if: the parser layer (Phase 2) finds enum DDL too painful to reason about and a CHECK-constraint variant would be a strictly cleaner test bed.

---

## 2026-05-21 — Seed volumes

Context: phase-1-plan.md targets ~1k users, ~800 accounts, ~1.5k subscriptions, ~50k transactions, ~200k events.

Decision: **Match the plan's targets.** Implementation choices inside seed.py:

- Plan tier distribution: 50% free, 30% pro, 15% team, 5% enterprise. Free accounts get no subscriptions.
- Subscription status distribution: 65% active, 10% trialing, 25% cancelled. Gives ~1100 in `fct_mrr`'s filter.
- Plan pricing in cents: pro $29 / team $99 / enterprise $499 monthly; yearly is monthly × 10.
- Expected MRR (rough back-of-envelope): ~$60-80k. Plausible for a small SaaS demo, not zero, not absurd.

Revisit if: `fct_mrr`'s output looks unrealistic when computed against the seeded data; the LLM eval cases later want subscription counts in a different shape.

---

## 2026-05-21 — Additional planted columns?

Context: `signup_date`, `amount_cents`, and the missing-`paused` enum value are the three planted columns. CLAUDE.md §5.4 asks if more should be planted now to give the eval set variety later.

Decision: **Hold for now; revisit at Phase 6 eval-set construction.**

Rationale: any additional planted column changes the SQL we have to write today (staging models need to consume it for the trap to bite later). Planting columns whose use-case isn't designed yet leads to dead code in `mock-analytics`. The three current planted columns already cover the three risk categories — structural, semantic-unit, enum. Wider eval variety can come from creative scenarios on existing columns (e.g., changing the default of `billing_interval`, adding a check constraint to `amount_cents`).

Candidates to keep in mind for Phase 6 if more variety is needed:
- `accounts.plan_tier` (string-with-check-constraint masquerading as enum) — could be migrated to a real enum, exercising the inverse of Scenario 3.
- `transactions.currency` — always 'USD' today; an FX scenario would test multi-currency aggregation.
- `events.properties` — schema-on-read JSONB; a "promote a JSON key to a column" scenario is realistic and semantic.

Revisit if: Phase 6 eval-set construction finds the 50 PRs feel monotonous.

---

## 2026-05-21 — No FastAPI surface beyond health checks

Context: phase-1-plan.md says "don't build real endpoints" — the API isn't the product.

Decision: **Two health-check endpoints only** (`GET /health`, `GET /health/db`).

Rationale: the migration history is the product. Time spent on CRUD endpoints does not advance any Phase 2+ goal. If a future demo needs a "real engineer changes the API alongside the schema" beat, that's a deliberate addition at the time, not speculative scaffolding now.

Revisit if: a scenario emerges where the demo needs PR changes that span API + migration + dbt.
