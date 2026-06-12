"""End-of-week DB check — confirms data is flowing into ai_company_signals."""

import db

# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

_BREAKDOWN_SQL = """
SELECT
    company_name,
    signal_type,
    COUNT(*) AS count
FROM ai_company_signals
GROUP BY company_name, signal_type
ORDER BY company_name, count DESC
"""

_TOTALS_SQL = """
SELECT
    COUNT(*)                                          AS total_signals,
    COUNT(DISTINCT company_name)                      AS unique_companies,
    MIN(signal_date)                                  AS earliest_signal,
    MAX(signal_date)                                  AS latest_signal,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') AS added_last_24h
FROM ai_company_signals
"""

_COLLECTOR_RUNS_SQL = """
SELECT
    collector_name,
    companies_processed,
    signals_added,
    errors,
    started_at,
    finished_at
FROM collection_runs
ORDER BY started_at DESC
LIMIT 10
"""


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _col_widths(*columns: list) -> list[int]:
    """Return the max width for each column position across all rows + header."""
    return [max(len(str(cell)) for cell in col) for col in columns]


def _print_table(headers: list[str], rows: list[tuple]) -> None:
    if not rows:
        print("  (no rows)")
        return

    cols = list(zip(headers, *rows))  # transpose so each element is one column
    widths = [max(len(str(cell)) for cell in col) for col in cols]

    sep   = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    fmt   = "| " + " | ".join(f"{{:<{w}}}" for w in widths) + " |"

    print(sep)
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*[str(c) for c in row]))
    print(sep)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    conn = db.get_connection()

    # --- Signal breakdown by company + type ---
    print("\n── Signal breakdown (company × signal_type) ──────────────────────\n")
    with conn.cursor() as cur:
        cur.execute(_BREAKDOWN_SQL)
        rows = cur.fetchall()

    _print_table(["company_name", "signal_type", "count"], rows)

    # --- Totals ---
    print("\n── Totals ─────────────────────────────────────────────────────────\n")
    with conn.cursor() as cur:
        cur.execute(_TOTALS_SQL)
        row = cur.fetchone()

    total_signals, unique_companies, earliest, latest, last_24h = row
    print(f"  Total signals      : {total_signals:,}")
    print(f"  Unique companies   : {unique_companies:,}")
    print(f"  Date range         : {earliest}  →  {latest}")
    print(f"  Added in last 24h  : {last_24h:,}")

    # --- Recent collector runs ---
    print("\n── Last 10 collector runs ─────────────────────────────────────────\n")
    with conn.cursor() as cur:
        cur.execute(_COLLECTOR_RUNS_SQL)
        run_rows = cur.fetchall()

    formatted_runs = [
        (
            r[0],                                          # collector_name
            r[1],                                          # companies_processed
            r[2],                                          # signals_added
            r[3],                                          # errors
            str(r[4])[:16] if r[4] else "—",              # started_at (trim to minute)
            str(r[5])[:16] if r[5] else "—",              # finished_at
        )
        for r in run_rows
    ]
    _print_table(
        ["collector", "companies", "signals", "errors", "started_at", "finished_at"],
        formatted_runs,
    )

    conn.close()
    print()


if __name__ == "__main__":
    main()
