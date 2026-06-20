"""Database connection helpers and upsert utilities for the collector layer."""

import os
import sys
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

_DATABASE_URL = os.getenv("DATABASE_URL")

_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS ai_company_signals (
  id                SERIAL PRIMARY KEY,
  company_name      TEXT NOT NULL,
  ticker            TEXT,
  signal_type       TEXT NOT NULL,
  signal_date       DATE,
  headline          TEXT,
  summary           TEXT,
  source_url        TEXT,
  importance_score  INT CHECK (importance_score BETWEEN 0 AND 100),
  raw_data          JSONB,
  langfuse_trace_id TEXT,
  created_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_company_signal
  ON ai_company_signals(company_name, signal_type);

CREATE INDEX IF NOT EXISTS idx_signal_date
  ON ai_company_signals(signal_date DESC);

CREATE INDEX IF NOT EXISTS idx_importance
  ON ai_company_signals(importance_score DESC);

CREATE TABLE IF NOT EXISTS collection_runs (
  id                  SERIAL PRIMARY KEY,
  collector_name      TEXT,
  companies_processed INT,
  signals_added       INT,
  errors              INT,
  started_at          TIMESTAMP,
  finished_at         TIMESTAMP
);
"""

_INSERT_SIGNAL_SQL = """
INSERT INTO ai_company_signals
  (company_name, ticker, signal_type, signal_date, headline, summary,
   source_url, importance_score, raw_data, langfuse_trace_id)
VALUES
  (%(company_name)s, %(ticker)s, %(signal_type)s, %(signal_date)s,
   %(headline)s, %(summary)s, %(source_url)s, %(importance_score)s,
   %(raw_data)s, %(langfuse_trace_id)s)
"""

_DUPLICATE_CHECK_SQL = """
SELECT 1 FROM ai_company_signals
WHERE company_name = %(company_name)s
  AND signal_type  = %(signal_type)s
  AND headline     = %(headline)s
  AND signal_date  = %(signal_date)s
LIMIT 1
"""

_GET_SIGNALS_SQL = """
SELECT id, company_name, ticker, signal_type, signal_date, headline,
       summary, source_url, importance_score, raw_data,
       langfuse_trace_id, created_at
FROM   ai_company_signals
WHERE  company_name = %(company_name)s
  AND  (%(signal_type)s IS NULL OR signal_type = %(signal_type)s)
  AND  signal_date >= CURRENT_DATE - %(days)s * INTERVAL '1 day'
ORDER  BY signal_date DESC, importance_score DESC
"""

_LOG_RUN_SQL = """
INSERT INTO collection_runs
  (collector_name, companies_processed, signals_added, errors,
   started_at, finished_at)
VALUES
  (%(collector_name)s, %(companies_processed)s, %(signals_added)s,
   %(errors)s, %(started_at)s, %(finished_at)s)
"""


def get_connection() -> psycopg2.extensions.connection:
    """Return a new psycopg2 connection using DATABASE_URL from the environment."""
    if not _DATABASE_URL:
        print(
            "ERROR: DATABASE_URL is not set.\n"
            "  1. Copy .env.example to .env in the project root.\n"
            "  2. Set DATABASE_URL, e.g.:\n"
            "       DATABASE_URL=postgresql://user:password@localhost:5432/mycroft\n"
            "  3. Make sure Postgres is running and the database exists."
        )
        sys.exit(1)

    try:
        conn = psycopg2.connect(_DATABASE_URL)
        return conn
    except psycopg2.OperationalError as exc:
        print(
            f"ERROR: Could not connect to Postgres.\n"
            f"  DATABASE_URL: {_DATABASE_URL}\n"
            f"  Underlying error: {exc}\n\n"
            "  Check that:\n"
            "    - Postgres is running (pg_isready or 'brew services list')\n"
            "    - The database named in DATABASE_URL exists\n"
            "    - The credentials in .env are correct"
        )
        sys.exit(1)


def create_tables() -> None:
    """Create all tables and indexes if they do not already exist."""
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(_CREATE_TABLES_SQL)
    finally:
        conn.close()


def insert_signal(
    company_name: str,
    ticker: str | None,
    signal_type: str,
    signal_date,
    headline: str,
    summary: str,
    source_url: str,
    importance_score: int,
    raw_data: dict | None = None,
    *,
    langfuse_trace_id: str | None = None,
) -> bool:
    """Insert a signal row, skipping duplicates.

    Returns True if the row was inserted, False if it already existed.
    """
    params = {
        "company_name": company_name,
        "ticker": ticker,
        "signal_type": signal_type,
        "signal_date": signal_date,
        "headline": headline,
        "summary": summary,
        "source_url": source_url,
        "importance_score": importance_score,
        "raw_data": psycopg2.extras.Json(raw_data or {}),
        "langfuse_trace_id": langfuse_trace_id,
    }

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(_DUPLICATE_CHECK_SQL, params)
                if cur.fetchone():
                    return False
                cur.execute(_INSERT_SIGNAL_SQL, params)
    finally:
        conn.close()

    return True


def get_signals(
    company_name: str,
    signal_type: str | None = None,
    days: int = 30,
) -> list[dict]:
    """Return recent signals for a company as a list of dicts."""
    params = {
        "company_name": company_name,
        "signal_type": signal_type,
        "days": days,
    }

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(_GET_SIGNALS_SQL, params)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def log_run(
    collector_name: str,
    companies_processed: int,
    signals_added: int,
    errors: int,
    started_at: datetime,
) -> None:
    """Record a completed collection run."""
    finished_at = datetime.now(tz=timezone.utc)
    params = {
        "collector_name": collector_name,
        "companies_processed": companies_processed,
        "signals_added": signals_added,
        "errors": errors,
        "started_at": started_at,
        "finished_at": finished_at,
    }

    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(_LOG_RUN_SQL, params)
    finally:
        conn.close()


if __name__ == "__main__":
    create_tables()
    print("Tables created.")
