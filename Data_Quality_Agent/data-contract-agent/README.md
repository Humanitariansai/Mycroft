# data-contract-agent

The agent that watches schema changes in [`mock-app-service`](../mock-app-service)
and warns when they will break — or silently corrupt — analytics models in
[`mock-analytics`](../mock-analytics).

This repo contains **Phase 2 (deterministic layer)** and **Phase 3 (LLM semantic
layer)**. No GitHub yet — a local CLI takes an Alembic migration (plus the PR's
title/description) and reports its downstream impact: what it can prove
mechanically, and what the LLM judges to be a *silent* semantic break.

## What it does

```
migration (.py) ──▶ migration_parser ──┐
                                        ├──▶ impact analyzer ──▶ findings
dbt manifest.json ─▶ lineage indexer ──┘
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

That split — deterministic vs. semantic — is the whole thesis of the project.

4. **`semantic`** *(Phase 3, LLM)* — reads the migration, the PR's stated intent, the
   deterministic findings, and the affected downstream SQL, and decides whether a change
   that *compiles cleanly* will silently corrupt a metric. Uses the Anthropic API
   (`claude-opus-4-8` by default) with a Pydantic-constrained structured output
   (`risk_category`, `affected_models`, `reasoning`, `confidence`). It degrades
   gracefully — if the LLM call fails, the deterministic findings still stand.

## Usage

```bash
pip install -e ".[dev]"

# deterministic only (no network), against the bundled fixtures
contract-agent fixtures/migrations/0003_subscriptions_amount.py \
    --manifest fixtures/manifest.json

# deterministic + LLM semantic layer (needs an API key)
export ANTHROPIC_API_KEY=sk-ant-...
contract-agent fixtures/migrations/0003_subscriptions_amount.py \
    --manifest fixtures/manifest.json \
    --pr fixtures/prs/0003_subscriptions_amount.json \
    --semantic
# optional: --model claude-sonnet-4-6   (cheaper for the 50-PR eval run)
```

## The three scenarios it's validated against

| Scenario | Migration | Verdict |
|---|---|---|
| 1. Rename `signup_date` → `created_at` | `0002_*` | **Structural break** — caught deterministically (3 models won't compile) |
| 2. `amount_cents` → `amount` (cents→dollars) | `0003_*` | **Structural break** (dropped column) **+ semantic review** (unit change handed to the LLM) |
| 3. Add `'paused'` to `subscription_status` | `0004_*` | **Enum review** — `fct_mrr`'s filter omits the value; rows drop silently → LLM |
| control. Add `users.phone` | `0005_*` | **No impact** (true negative) |

## Tests

```bash
pytest        # parser, column-level lineage, impact, + semantic context assembly
ruff check .
```

The 3 live LLM tests (`test_semantic.py`) auto-skip unless `ANTHROPIC_API_KEY` is set.

## Not in this repo yet

Phase 4 (GitHub App + webhook) and the 50-PR labeled eval set live in later
phases. The deterministic layer is designed to produce useful output even when
the LLM call fails.
