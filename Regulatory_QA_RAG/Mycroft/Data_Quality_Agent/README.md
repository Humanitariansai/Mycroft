# Data Contract Agent

An agent that watches schema changes in an operational backend and warns when they
will **silently corrupt** downstream analytics — *before* the PR merges.

The hard problem isn't the breaks that crash. It's the ones that **compile, run,
pass every test, and return a number that is quietly wrong**. This project builds a
two-layer agent for exactly those: a deterministic layer that traces column-level
lineage and proves structural impact, and a focused LLM layer that reads the change's
intent and judges whether it's a silent semantic break.

> **Thesis:** use deterministic tooling for the mechanical half (what changed, what it
> feeds) and confine the LLM to the one thing machines are bad at — reading intent.
> The seam between those two layers is the whole point.

---

## The three demo scenarios

Each is a realistic PR against the operational schema. They get progressively nastier:

| # | Change | What breaks | Who catches it |
|---|---|---|---|
| **1. Structural** | rename `users.signup_date` → `created_at` | analytics fails to compile — loud | **deterministic layer** |
| **2. Semantic unit** | `amount_cents` → `amount` (cents→dollars), `/100` left in staging | nothing crashes; **MRR is 100× wrong** | **LLM layer** |
| **3. Enum expansion** | add `'paused'` to `subscription_status` | `fct_mrr` filter omits it; rows silently vanish | **hybrid** |

Verified ground truth (deterministic seed): baseline MRR is **$108,176.33**; after
Scenario 2 it collapses to **$1,081.76**; after Scenario 3 it drops to **$91,587.67**.

---

## Repository layout

```
Data-Quality_project/
├── README.md                ← you are here (overview + how to test)
├── CLAUDE.md                ← Phase 0 design brief
├── project-plan.md          ← thesis, architecture, build phases
├── phase-1-plan.md          ← detailed Phase 1 plan
│
├── mock-app-service/        ← (1) operational backend: FastAPI + Postgres + Alembic
│   ├── app/models/          ←     5 tables; the three "trap" columns live here
│   ├── alembic/versions/    ←     baseline migration
│   ├── scripts/seed.py      ←     synthetic data (Faker)
│   └── docker-compose.yml   ←     Postgres
│
├── mock-analytics/          ← (2) dbt project (DuckDB) computing the metrics
│   ├── models/staging/      ←     stg_* views mirroring sources
│   ├── models/marts/        ←     fct_mrr, fct_revenue, dim_users, fct_engagement
│   └── scripts/             ←     Postgres → Parquet loader
│
└── data-contract-agent/     ← (3) THE AGENT
    ├── contract_agent/
    │   ├── migration_parser.py   ← AST-parse Alembic → structured changes
    │   ├── lineage.py            ← sqlglot over dbt manifest → column lineage
    │   ├── impact.py             ← join → categorized findings (deterministic)
    │   ├── semantic.py           ← LLM layer (Anthropic API) → silent-break verdict
    │   └── cli.py                ← `contract-agent` entrypoint
    ├── fixtures/            ←     3 scenario migrations + control + PR text + manifest
    └── tests/              ←     parser, lineage, impact, semantic
```

`mock-app-service` is where schema changes are born; `mock-analytics` is what breaks;
`data-contract-agent` is the agent that watches the boundary between them. They are
**separate by design** — that separation is the reason the bug class exists in real life.

---

## Prerequisites

- **Docker Desktop** (provides Postgres — no local Postgres install needed)
- **Python 3.11+**
- **An Anthropic API key** (`ANTHROPIC_API_KEY`) — only for the LLM layer (Phase 3)

Each sub-project uses its own virtualenv; nothing is installed globally.

---

## How to test this product

There are three independent things you can verify. Phase 1 proves the traps are real;
Phase 2 proves the deterministic layer catches what it should; Phase 3 proves the LLM
catches the silent break that nothing else can.

### Phase 1 — the data pipeline + the traps (no API key needed)

```bash
# 0. Start Docker Desktop first, then:

# 1. Bring up Postgres
cd mock-app-service
docker compose up -d postgres

# 2. App venv → create tables → seed ~1k users / 1.5k subs / ~49k txns / 200k events
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
export DATABASE_URL=postgresql+psycopg2://mock:mock@localhost:5432/mock
alembic upgrade head
python scripts/seed.py
deactivate

# 3. Export Postgres → Parquet, then build the dbt warehouse
cd ../mock-analytics
python3 -m venv .venv && source .venv/bin/activate
pip install -e .            # installs dbt-duckdb
export PG_URL=postgresql://mock:mock@localhost:5432/mock
python scripts/load_from_postgres.py
dbt build                   # expect: PASS=59, ERROR=0
```

**Expected:** `dbt build` is green, and `fct_mrr` totals **$108,176.33** across 1,152
active+trialing subscriptions. Stop Postgres anytime with `docker compose down` in
`mock-app-service/` (add `-v` to wipe the seeded data).

### Phase 2 — the deterministic layer (no API key needed)

```bash
cd ../data-contract-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run the agent against each scenario (uses the bundled manifest fixture)
contract-agent fixtures/migrations/0002_rename_signup_date.py        --manifest fixtures/manifest.json
contract-agent fixtures/migrations/0003_subscriptions_amount.py      --manifest fixtures/manifest.json
contract-agent fixtures/migrations/0004_subscription_status_paused.py --manifest fixtures/manifest.json
contract-agent fixtures/migrations/0005_add_user_phone.py            --manifest fixtures/manifest.json  # control

pytest        # parser, column-level lineage, impact classification
```

**Expected:** Scenario 1 → `STRUCTURAL BREAK` (3 models); Scenario 2 → `STRUCTURAL BREAK`
+ `SEMANTIC REVIEW` (unit risk); Scenario 3 → `ENUM REVIEW`; control → no impact.

### Phase 3 — the LLM semantic layer (needs an API key)

```bash
# still in data-contract-agent, with the venv active
export ANTHROPIC_API_KEY=sk-ant-...

contract-agent fixtures/migrations/0003_subscriptions_amount.py \
    --manifest fixtures/manifest.json \
    --pr fixtures/prs/0003_subscriptions_amount.json \
    --semantic
# optional, cheaper: --model claude-sonnet-4-6

pytest        # the 3 live LLM tests now run (they auto-skip without a key)
```

**Expected:** Scenario 2 → `⚠ SEMANTIC BREAK  category=unit_change`; Scenario 1 → `✓ no
semantic break`; control → `✓ no semantic break`. This is the headline result — the agent
flags the 100×-wrong MRR from a PR that looks like routine cleanup.

---

## Status

| Phase | What | State |
|---|---|---|
| 0 | Design lock (schema, scenarios, decisions) | ✅ done |
| 1 | Mock repos + dbt pipeline; traps proven by hand | ✅ done & verified |
| 2 | Deterministic layer (parser + lineage + impact) | ✅ done; tests green |
| 3 | LLM semantic analyzer | ✅ built; run live with an API key |
| 4 | GitHub App (webhook → comment on PR) | ⬜ not started |
| 6 | 50-PR labeled eval set; target **F1 ≥ 0.8** | ⬜ not started |

See [project-plan.md](project-plan.md) for the full thesis and build sequence.
