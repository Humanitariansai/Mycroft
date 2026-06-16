# mock-app-service

The operational backend half of the data contract agent demo. A FastAPI + SQLAlchemy + Alembic + Postgres app that mimics a SaaS engineering codebase. **Schema changes originate here.** A sibling dbt project (`mock-analytics`) consumes the schema; the data contract agent watches PRs against this repo and warns about downstream impact.

This repo is a prop. The migration history is the product.

## Tables

`users`, `accounts`, `subscriptions`, `transactions`, `events`. See [docs/schema.md](docs/schema.md) for column-level definitions and the three demo "trap" columns (`users.signup_date`, `subscriptions.amount_cents`, `subscriptions.status` enum).

## Quickstart

```bash
docker compose up -d postgres
docker compose run --rm app alembic upgrade head
docker compose run --rm app python scripts/seed.py
docker compose up app
```

Health check: `curl http://localhost:8000/health`.

### Local (no Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DATABASE_URL=postgresql+psycopg2://mock:mock@localhost:5432/mock
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

## Docs

- [docs/schema.md](docs/schema.md) — table definitions and the planted "refactorable" columns.
- [docs/scenarios.md](docs/scenarios.md) — three demo scenarios as drafted commits.
- [docs/decision-log.md](docs/decision-log.md) — non-obvious decisions made during Phase 0 / Phase 1.
