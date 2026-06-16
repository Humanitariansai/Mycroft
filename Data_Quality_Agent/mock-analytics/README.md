# mock-analytics

dbt project (DuckDB) consuming `mock-app-service`'s Postgres schema. The downstream half of the data contract agent demo.

## Layout

```
models/
  staging/   # one stg_ model per source table; thin renames + type casts
  marts/     # fct_mrr, fct_revenue, dim_users, fct_engagement
sources.yml  # declares operational tables as sources (read from raw/*.parquet)
scripts/
  load_from_postgres.py  # extracts Postgres tables → raw/*.parquet
```

## The cross-DB seam

`dbt-duckdb` can't usefully read Postgres directly. Instead, `scripts/load_from_postgres.py` does the equivalent of an EL tool — `SELECT * FROM <table>` against Postgres, writes Parquet into `raw/`, and the DuckDB source declarations point at those files. This keeps the demo self-contained and mirrors real Fivetran-style "raw tables in the warehouse" workflows.

## Quickstart

Assuming `mock-app-service` Postgres is running with seeded data on `localhost:5432`:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Extract Postgres → Parquet
export PG_URL=postgresql://mock:mock@localhost:5432/mock
python scripts/load_from_postgres.py

# Build and compile
dbt build --profiles-dir .

# Inspect the manifest column-level lineage
ls target/manifest.json
```

The headline metric:

```bash
duckdb mock_analytics.duckdb -c "SELECT round(sum(monthly_amount_usd), 2) AS mrr FROM fct_mrr"
```

## Profile

`profiles.yml` is checked into the repo root and targets DuckDB at `./mock_analytics.duckdb`. No secrets — it's a demo.
