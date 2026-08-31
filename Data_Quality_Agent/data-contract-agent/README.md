# data-contract-agent

The agent that watches schema changes in [`mock-app-service`](../mock-app-service)
and warns when they will break — or silently corrupt — analytics models in
[`mock-analytics`](../mock-analytics).

This repo contains **Phase 2 (deterministic layer)**, **Phase 3 (LLM semantic
layer)**, and the **metric-impact simulation**. No GitHub yet — a local CLI takes an
Alembic migration (plus the PR's title/description) and reports its downstream impact:
what it can prove mechanically, what it can *measure* by rebuilding the marts, and what
the LLM judges to be a *silent* semantic break.

## What it does

```
migration (.py) ──▶ migration_parser ──┐
                                        ├──▶ impact analyzer ──▶ findings
dbt manifest.json ─▶ lineage indexer ──┘         │
                                                 └──▶ simulate ──▶ metric diff
```

1. **`migration_parser`** — statically parses an Alembic migration with the stdlib
   `ast` module (never executes it). Extracts column adds/drops/renames/retypes,
   enum `ADD VALUE`s, and raw backfill SQL.
2. **`lineage`** — parses every model's `compiled_code` from the dbt manifest with
   [sqlglot](https://github.com/tobymao/sqlglot) and reconstructs **column-level**
   lineage, tracing each mart column back through staging to the operational source
   column that feeds it.
3. **`impact`** — joins the two. It separates what it can *prove* (a dropped/renamed
   column a model reads **will** break) from what it can only *surface* for the
   semantic/LLM layer (a unit-suffix change with an arithmetic backfill; an enum
   value an `IN (...)` filter doesn't cover).
4. **`simulate`** — stands up a throwaway DuckDB warehouse, materializes the dbt DAG
   straight from the manifest's `compiled_code`, replays the migration onto the source
   tables, rebuilds, and **diffs the marts**. This is the layer that turns
   *"`fct_mrr` may be silently wrong"* into *"`fct_mrr` goes 108,176.33 → 1,081.76"*.
5. **`semantic`** *(Phase 3, LLM)* — reads the migration, the PR's stated intent, the
   deterministic findings, and the affected downstream SQL, and decides whether a change
   that *compiles cleanly* will silently corrupt a metric. Uses the Anthropic API
   (`claude-opus-4-8` by default) with a Pydantic-constrained structured output
   (`risk_category`, `affected_models`, `reasoning`, `confidence`). It degrades
   gracefully — if the LLM call fails, the deterministic findings still stand.

That split — deterministic vs. semantic — is the whole thesis of the project, and
`simulate` is what keeps both halves honest: it measures the damage instead of
asserting it.

## Usage

```bash
pip install -e ".[dev]"

# deterministic only (no network), against the bundled fixtures
contract-agent fixtures/migrations/0003_subscriptions_amount.py \
    --manifest fixtures/manifest.json

# deterministic + metric-impact simulation (no network, no API key, no Docker)
contract-agent fixtures/migrations/0003_subscriptions_amount.py \
    --manifest fixtures/manifest.json \
    --simulate

# deterministic + LLM semantic layer (needs an API key)
export ANTHROPIC_API_KEY=sk-ant-...
contract-agent fixtures/migrations/0003_subscriptions_amount.py \
    --manifest fixtures/manifest.json \
    --pr fixtures/prs/0003_subscriptions_amount.json \
    --semantic
# optional: --model claude-sonnet-4-6   (cheaper for the 50-PR eval run)
```

## Metric-level impact simulation (`--simulate`)

The deterministic layer proves *structure*; the LLM layer reasons about *intent*.
Neither tells you what the dashboard will actually say. `--simulate` does:

```
    Build as-is — the loud half, what CI would show you:
      x stg_subscriptions: BinderException: Referenced column "amount_cents" not found
      x fct_mrr: blocked by upstream failure in stg_subscriptions

    Then applied the mechanical fix a reviewer would make (amount_cents -> amount in
    stg_subscriptions) and rebuilt. The numbers do not survive:

      fct_mrr
        sum(monthly_amount_usd)           11,190.00 ->           111.90   x0.01

    ! fct_mrr: monthly_amount_usd rescaled by x0.01 (100x off) while still compiling
```

**Why two builds.** Scenario 2 drops `amount_cents`, so a naive replay just fails to
compile — the loud half, which tells you nothing new. Nobody ships a red pipeline: a
reviewer renames the column in the staging model and moves on. The 100x error only
appears *after* that fix, so the simulation applies that mechanical rename itself
(`--no-auto-patch` to skip it) and diffs the result. The patch is scoped by lineage,
not by name — `transactions.amount_cents` shares a name with the renamed column and
must not be touched.

**Enum expansion is projected, not replayed.** `ALTER TYPE ... ADD VALUE` changes no
rows on the day it merges; the damage arrives when the application starts writing the
value. So the simulation moves `--enum-shift` (default 10%) of the rows a downstream
filter currently *accepts* into the new value, labels the result a counterfactual, and
reports a per-1% sensitivity you can scale to your own adoption estimate.

**Where the data comes from.** By default a deterministic synthetic seed built from the
baseline migration's schema — no Docker, no Postgres, no dbt run, ~2s. Point
`--sources ../mock-analytics/raw` at the real Parquet extract to get the exact numbers
from the README ($108,176.33 → $1,081.76). The absolute values differ between the two;
the ratios, which are what the finding rests on, do not.

Needs the `sim` extra (`pip install -e ".[sim]"`) for DuckDB. Like the LLM layer, it
degrades gracefully — if the simulation can't run, the deterministic findings stand.

## The three scenarios it's validated against

| Scenario | Migration | Verdict | What `--simulate` measures |
|---|---|---|---|
| 1. Rename `signup_date` → `created_at` | `0002_*` | **Structural break** — caught deterministically (3 models won't compile) | 3 models fail; after the rename, **zero** metric drift — loud but safe |
| 2. `amount_cents` → `amount` (cents→dollars) | `0003_*` | **Structural break** (dropped column) **+ semantic review** (unit change handed to the LLM) | after the rename everything compiles and `fct_mrr` is **×0.01** |
| 3. Add `'paused'` to `subscription_status` | `0004_*` | **Enum review** — `fct_mrr`'s filter omits the value; rows drop silently → LLM | counterfactual: 10% adoption drops `fct_mrr` rows and revenue, with per-1% sensitivity |
| control. Add `users.phone` | `0005_*` | **No impact** (true negative) | every model rebuilds, every metric identical |

## Tests

```bash
pytest        # parser, lineage, impact, simulation, + semantic context assembly
ruff check .
```

`test_simulate.py` asserts on *ratios* (×0.01, rows dropped) rather than absolute
values, so the same tests pass against the synthetic seed and against real seeded
data. The 3 live LLM tests (`test_semantic.py`) auto-skip unless `ANTHROPIC_API_KEY`
is set; the simulation tests skip if the `sim` extra isn't installed.

## Not in this repo yet

Phase 4 (GitHub App + webhook) and the 50-PR labeled eval set live in later
phases. Every layer is designed to produce useful output when the one above it
fails: the deterministic findings stand without the simulation, and both stand
without the LLM call.
