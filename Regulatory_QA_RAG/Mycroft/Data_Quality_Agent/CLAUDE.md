# CLAUDE.md — mock-app-service

> Phase 0 scope. Treat this file as the brief for the **design-lock phase** of this repo only. Do **not** start writing application code yet. The output of this phase is documents and decisions, not features.

---

## 1. What this repo is

`mock-app-service` is the **operational backend** half of a two-repo demo for a data contract agent. It mimics a real SaaS engineering codebase where schema changes originate. A sibling repo, `mock-analytics`, consumes its schema via dbt.

**The whole point of two repos** is that operational engineers ship a schema change here, and analytical models break (or worse, silently produce wrong numbers) over there. The agent being built in a third repo watches PRs against *this* repo and warns about downstream impact in *that* repo.

Stack for this repo:

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Alembic for migrations
- Postgres (operational DB)
- pytest, ruff, pyright/mypy

The dbt analytics repo will consume Postgres directly, OR via a DuckDB copy of the schema — this is an open decision (see §5).

---

## 2. Cross-repo context (read once, then anchor on this repo)

```
┌─────────────────────┐         ┌─────────────────────┐
│  mock-app-service   │         │   mock-analytics    │
│  (this repo)        │         │   (dbt project)     │
│                     │         │                     │
│  FastAPI + Alembic  │ ──schema──>│ staging → marts │
│  Postgres           │         │   manifest.json     │
└─────────────────────┘         └─────────────────────┘
            │                              │
            │  PR webhook                  │  manifest fetch
            ▼                              ▼
        ┌──────────────────────────────────────┐
        │   data-contract-agent (third repo)   │
        │   migration parser + lineage + LLM   │
        └──────────────────────────────────────┘
```

You only work in the left box. But every schema decision you make has to support three demo scenarios that hit the right box:

1. **Structural break**: rename `users.signup_date` → `users.created_at`. Staging model fails at compile time.
2. **Semantic unit break**: `subscriptions.amount_cents` (int, cents) → `subscriptions.amount` (numeric, dollars), with a backfill dividing by 100. Type and constraints look fine; `fct_mrr` is silently wrong by 100x.
3. **Enum expansion**: add `'paused'` to `subscription_status` enum. `fct_mrr` filters `status IN ('active', 'trialing')` and silently drops the new value.

If the Phase 0 schema doesn't make all three of these natural, plausible commits, the schema is wrong. Redo it.

---

## 3. Phase 0 deliverables (this is the entire job for now)

Produce these files in the repo root under `docs/`:

### 3.1 `docs/system-diagram.md`

One-page Mermaid diagram of the three-repo system. Must show:

- The two mock repos and the agent repo as distinct boxes.
- Data flow: PR event → webhook → migration parser → lineage map → LLM → PR comment.
- Where `manifest.json` lives and how it gets to the agent (GitHub Action on `mock-analytics` main → S3 or metadata branch).
- The seam between deterministic layer and LLM layer, drawn explicitly. This seam is the thesis of the project; the diagram must make it visually obvious.

### 3.2 `docs/schema.md`

Final table definitions for: `users`, `accounts`, `subscriptions`, `transactions`, `events`.

For each table:

- Columns with Postgres types and constraints.
- Primary key, foreign keys, indexes.
- Enum types defined separately at the top of the doc.
- A one-line note on which downstream mart(s) consume it.

Constraints on the design:

- `subscriptions` must contain a monetary column whose name and unit can plausibly change in a PR (scenario 2). Start it as `amount_cents BIGINT NOT NULL`. The fact that "cents" is in the name is load-bearing for the demo.
- `subscriptions` must have a `status` column of a Postgres `ENUM` type with initial values `('active', 'trialing', 'cancelled')`. The migration in scenario 3 will add `'paused'`.
- `users` must have a timestamp column initially named `signup_date` (scenario 1 renames it). Yes, this is a slightly weird name. That's the point — it's the kind of name a junior eng would "clean up."
- Every mart needs to depend on at least two source tables, so column-level lineage is non-trivial.

### 3.3 `docs/mart-contracts.md`

The four mart models defined in the plan: `fct_mrr`, `fct_revenue`, `dim_users`, `fct_engagement`.

For each:

- Grain (one row per what).
- Source columns consumed (table.column form). This is the column-level lineage the deterministic layer will reconstruct.
- The metric definition in English **and** in pseudo-SQL.
- For `fct_mrr` specifically: the filter on `subscription_status` must be written out explicitly as `status IN ('active', 'trialing')` so scenario 3 is a real bug.
- For `fct_mrr` and `fct_revenue`: the unit (cents vs dollars) must be stated, so scenario 2 is a real bug.

This file is the **data contract** the agent is going to learn to defend. Treat it that way.

### 3.4 `docs/scenarios.md`

Each of the three demo scenarios written as an ordered sequence of commits on a feature branch in this repo:

1. The Alembic migration file (full Python, not pseudocode).
2. The corresponding model change in `app/models/`.
3. The PR title and PR description text — write these as a real engineer would. The PR description is an input to the LLM layer; quality matters. Scenario 2's description should be plausibly innocent ("standardize amount column for new pricing tables") — the whole point is that a human reviewer would miss it.

These are **drafts** in Phase 0, not executed. They get committed for real in Phase 1+ once the schema and models exist.

### 3.5 `docs/decision-log.md`

Append-only log. One entry per non-obvious decision made during Phase 0. Format:

```
## YYYY-MM-DD — <decision title>
Context: <what forced the decision>
Options considered: <list>
Decision: <chosen option>
Rationale: <why>
Revisit if: <condition that would re-open this>
```

Seed it with the open decisions from §5.

### 3.6 `docs/eval-set-spec.md`

A short spec — not the data — for the 50-PR labeled evaluation set. Define:

- Label schema (binary: contains semantic break y/n; plus risk category if y).
- Per-PR artifact format (diff, PR title, PR description, expected label, expected agent output).
- Stratification: how many of each scenario type, how many control PRs with no break.
- Storage location and naming convention.

The eval set itself is built in Phase 6. The *spec* is locked now, because the schema design has to be able to support 50 distinct realistic PRs against it.

---

## 4. Repo layout to create in Phase 0

```
mock-app-service/
├── CLAUDE.md                    # this file
├── README.md                    # one-paragraph overview + link to docs/
├── docs/
│   ├── system-diagram.md
│   ├── schema.md
│   ├── mart-contracts.md
│   ├── scenarios.md
│   ├── decision-log.md
│   └── eval-set-spec.md
├── pyproject.toml               # tool config only, no deps installed yet — Phase 1
└── .gitignore
```

Do **not** create `app/`, `alembic/`, `tests/`, or any Python source files in Phase 0. The temptation will be strong. Resist it. Phase 0 ends when the docs above are reviewed and the schema in `schema.md` is one a real SaaS engineer would believe.

---

## 5. Open decisions to resolve in this phase

Write these into `docs/decision-log.md` with a tentative call + a "revisit if" trigger. None of these block Phase 1, but they all need a tentative answer before Phase 1 starts.

1. **DuckDB vs Postgres for the analytics layer.** Plan currently leans DuckDB for MVP, Postgres if it becomes a problem. Confirm.
2. **Enum type implementation.** Postgres native `ENUM` vs `VARCHAR + CHECK constraint`. Native ENUM makes the migration in scenario 3 more interesting (it uses `ALTER TYPE ... ADD VALUE`), which is the realistic case. Recommend native ENUM. Confirm.
3. **Seed data volume.** Enough rows to make `fct_mrr` produce a plausible number, not so many that local Postgres setup is slow. Target: ~1k users, ~2k subscriptions, ~20k transactions, ~100k events. Confirm or revise.
4. **Naming convention for the "obviously refactorable" columns.** `signup_date`, `amount_cents` are the two planted ones. Are there others worth planting now so the eval set has variety later? List candidates.

---

## 6. Working agreements with Claude Code

- **Do not skip ahead.** If a Phase 1+ task is tempting, write it as a TODO in `docs/decision-log.md` instead.
- **Ask before guessing on schema.** If a column type, constraint, or relationship is ambiguous, stop and ask. Schema mistakes here propagate into every downstream artifact.
- **Mermaid for diagrams**, not ASCII, not images. The diagram lives in version control and gets reviewed in PRs.
- **Write the PR descriptions in `scenarios.md` as a human would.** No "this PR seeds scenario 2." Real engineers do not narrate their own bugs. Scenario 2's PR description in particular has to read like a routine refactor.
- **Match the resume framing.** Every doc should be something a hiring manager could read and immediately see what the project is about. No internal jargon without a one-line gloss.

---

## 7. Definition of done for Phase 0

A second person (or a fresh Claude Code session) can read `docs/` and:

1. Draw the same system diagram.
2. Write the three Alembic migrations from scenario.md without further context.
3. Predict what `fct_mrr` will output before and after each scenario's migration.
4. Identify which scenarios the deterministic layer alone catches and which need the LLM.

When all four are true, Phase 0 is done. Start Phase 1.
