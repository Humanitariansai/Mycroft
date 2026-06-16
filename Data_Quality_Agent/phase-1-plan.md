# Phase 1 Plan: Mock Repos

**Goal:** two repos that produce a realistic dbt manifest with column-level lineage across staging and marts, seeded with data that makes the three demo scenarios meaningful. No agent code yet.

---

## Scope check before starting

A few things to lock from Phase 0 that Phase 1 depends on. If any are still open, resolve them first — they're cheap decisions but expensive to reverse mid-build:

- **DuckDB vs Postgres for analytics.** Recommend DuckDB. Faster local demo, no container, dbt-duckdb is mature. Postgres-as-warehouse is closer to production but you're already running Postgres as the *operational* DB; using it for both muddies the demo's point about the cross-system boundary.
- **Operational schema is final.** `users`, `accounts`, `subscriptions`, `transactions`, `events` — column lists locked. Changing these after seeding means re-seeding.
- **Mart definitions are final enough to write SQL against.** `fct_mrr`, `fct_revenue`, `dim_users`, `fct_engagement` — you need to know what each one computes before you can write the staging models it depends on.

---

## mock-app-service

The operational repo. FastAPI + SQLAlchemy + Alembic + Postgres.

### Structure

```
mock-app-service/
  app/
    models/         # SQLAlchemy ORM
    api/            # FastAPI routes (minimal — health check + maybe one CRUD endpoint per table)
    db.py
  alembic/
    versions/       # initial migration creating all five tables
    env.py
  scripts/
    seed.py         # generates synthetic data
  docker-compose.yml  # postgres + the app
  pyproject.toml
```

### What to actually build

1. SQLAlchemy models for the five tables. Realistic columns:
   - `subscriptions.amount_cents` (integer, deliberately in cents to set up Scenario 2)
   - `subscriptions.status` as a Postgres enum with values `active`, `trialing`, `cancelled` (deliberately missing `paused` to set up Scenario 3)
   - `users.signup_date` (deliberately named this way to set up Scenario 1)
2. One initial Alembic migration that creates everything. This is the baseline — the three scenario migrations come later as separate PRs.
3. `seed.py` using Faker. Targets: ~1000 users, ~800 accounts, ~1500 subscriptions across the three statuses, ~50k transactions, ~200k events. Enough volume that downstream marts have non-trivial numbers.
4. docker-compose to bring up Postgres and run migrations + seed in one command.

### What NOT to build

Real auth, real API surface beyond a health check, tests beyond "the seed script runs and the row counts look right." This repo is a prop. The migrations are the product.

---

## mock-analytics

The dbt repo. DuckDB.

### Structure

```
mock-analytics/
  models/
    staging/
      stg_users.sql
      stg_accounts.sql
      stg_subscriptions.sql
      stg_transactions.sql
      stg_events.sql
    marts/
      dim_users.sql
      fct_mrr.sql
      fct_revenue.sql
      fct_engagement.sql
  seeds/             # optional: small reference data like plan tiers
  sources.yml        # declares the operational tables as sources
  dbt_project.yml
  profiles.yml       # DuckDB target
  scripts/
    load_from_postgres.py   # extracts operational DB → DuckDB
```

### The cross-DB question

dbt-duckdb can't read Postgres directly in a useful way for this. Easiest path: a small Python script that does `SELECT * FROM <each table>` against Postgres and writes Parquet files into a `raw/` directory, and the DuckDB source declarations point at those Parquet files. This mirrors what real EL tools do (Fivetran lands raw tables in the warehouse) and keeps the demo self-contained.

### What each model needs to do — and why each matters for the scenarios

- **`stg_subscriptions`** — renames `amount_cents` to a column the marts use, casts to dollars. **This is the layer where Scenario 2 hides:** if the operational column changes from `amount_cents` to `amount` and the staging model's division-by-100 stays in place, `fct_mrr` is wrong by 100x. The staging model needs to do the cents→dollars conversion *as it exists today* for the scenario to be a real trap.
- **`stg_subscriptions`** also filters or surfaces `status`. **Scenario 3 hides downstream:** `fct_mrr`'s `WHERE status IN ('active', 'trialing')` is the actual trap. Make sure that filter is in `fct_mrr`, not buried in staging.
- **`stg_users`** selects `signup_date`. **Scenario 1 hits here:** renaming the source column breaks this model at compile time. Good — that's the baseline scenario.
- **`fct_mrr`** — the showpiece. Joins `stg_subscriptions`, filters active/trialing, sums monthly amount. Should produce a realistic MRR number from the seed data.
- **`fct_revenue`, `fct_engagement`, `dim_users`** — supporting marts. Don't need to be elaborate, but need real column-level lineage to the staging layer so the lineage indexer has something to chew on later.

### Manifest verification

The whole point of this repo is to produce a `target/manifest.json` with column-level lineage that Phase 2 can parse. After `dbt compile`, open the manifest and check that:

- The five staging models reference their sources.
- The marts reference the staging models.
- `compiled_code` is populated (sqlglot needs this in Phase 2).

If column-level lineage is thin because the SQL is too simple, the Phase 2 lineage indexer will look more impressive than it is. Write the SQL with realistic joins and CTEs.

---

## Verification gate before declaring Phase 1 done

Concrete checks, not vibes:

1. `docker-compose up` in mock-app-service brings up Postgres, runs the initial migration, runs the seed, and exits cleanly.
2. `python scripts/load_from_postgres.py` in mock-analytics produces Parquet files in `raw/`.
3. `dbt build` runs green against the seeded data.
4. `fct_mrr` returns a number that looks like real MRR (not zero, not absurd) given the seed volume.
5. `target/manifest.json` exists and contains column-level references from marts → staging → sources.
6. **The scenario trap is loaded:** if you manually rename `signup_date` in the SQLAlchemy model, regenerate the migration, re-run, and re-run dbt — `stg_users` fails to compile. If you manually change `amount_cents` to `amount` (with a backfill) and update only the operational side, `fct_mrr` still compiles and returns a wrong number. Verifying this by hand *before* the agent exists is the point — it proves the scenarios are real before you build something to detect them.

That last check is the one to actually run. It's the cheapest way to confirm Phase 1 has set up the trap correctly, and it gives you the ground-truth "wrong by 100x" number to compare against when Phase 3's LLM eventually flags the PR.

---

## Time estimate

Realistic: a long weekend, or two evenings + a Saturday. The trap to watch for: spending too long on the FastAPI side. The API isn't the product; the migration history is. If you find yourself building real endpoints, stop.

---

## What's deferred to later phases

- The three scenario migrations as separate PRs — that's Phase 2 input, not Phase 1 setup. Phase 1 ends with the baseline state.
- Any GitHub Actions wiring — Phase 4.
- Caching the manifest in S3 or a metadata branch — Phase 2 / Phase 4.
