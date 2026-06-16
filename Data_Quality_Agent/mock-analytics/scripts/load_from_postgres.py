"""Extract operational tables from Postgres → Parquet in ./raw/.

This is the EL seam between mock-app-service (operational Postgres) and
mock-analytics (DuckDB warehouse). In production this would be Fivetran /
Airbyte / dlt landing raw tables in the warehouse. For the demo, a small
Python script is enough.

Usage:
    export PG_URL=postgresql://mock:mock@localhost:5432/mock
    python scripts/load_from_postgres.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import psycopg2

TABLES = ["users", "accounts", "subscriptions", "transactions", "events"]

PG_URL = os.environ.get("PG_URL", "postgresql://mock:mock@localhost:5432/mock")
RAW_DIR = Path(__file__).resolve().parent.parent / "raw"


def extract_table(conn: psycopg2.extensions.connection, table: str, out_dir: Path) -> int:
    out_path = out_dir / f"{table}.parquet"
    # Cast enum columns to text so DuckDB reads them as varchar (otherwise
    # parquet writes them as bytes/dict and downstream casts get awkward).
    df = pd.read_sql(f"SELECT * FROM {table}", conn)

    # Coerce any object columns whose values are enums (psycopg2 returns enums
    # as plain strings already, so this is usually a no-op).
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype("string")

    df.to_parquet(out_path, index=False)
    return len(df)


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Extracting from {PG_URL!r} → {RAW_DIR}", flush=True)

    with psycopg2.connect(PG_URL) as conn:
        for table in TABLES:
            n = extract_table(conn, table, RAW_DIR)
            print(f"  {table:<15} {n:>8,} rows", flush=True)

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
