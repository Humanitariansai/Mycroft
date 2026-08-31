"""Metric-level impact simulation — prove the number changed.

The deterministic layer proves *structure* ("3 models read this column") and the
LLM layer reasons about *intent* ("this looks like a cents -> dollars change").
Neither of them can tell you what the CFO's dashboard will actually say on Monday.

This layer can. It stands up a throwaway DuckDB warehouse, materializes the whole
dbt DAG straight from the manifest's ``compiled_code``, replays the parsed
migration onto the source tables, rebuilds, and diffs the marts. Instead of

    fct_mrr may be silently wrong

you get

    fct_mrr  sum(monthly_amount_usd)   108,176.33 -> 1,081.76   (x0.01)

The subtlety that makes this work
---------------------------------
Scenario 2's migration drops ``amount_cents``, so on a naive replay every model
that reads it simply fails to compile — which is the *loud* half of the break and
tells you nothing new. But nobody ships a red pipeline: a reviewer mechanically
renames the column in the staging model and moves on. The silent 100x error only
appears *after* that fix.

So the simulation runs two builds:

  1. **as-is** — which models fail outright (the loud, structural half), and
  2. **post-fix** — the same build with the mechanical rename a reviewer would
     apply (:func:`contract_agent.impact.infer_renames` supplies the old -> new
     mapping), which is where the silent corruption surfaces.

Enum expansion is different in kind: ``ALTER TYPE ... ADD VALUE`` changes no rows
today, so there is nothing to replay. The damage arrives later, when the
application starts *writing* the new value. For that case the simulation runs an
explicitly-labelled counterfactual — move a fraction of the rows a downstream
filter currently accepts into the new value — and reports the resulting drop plus
a per-1% sensitivity, so the projection can be scaled to any adoption estimate.

Data sources, in order of preference:
  * ``--sources <dir>``  a directory of ``<table>.parquet`` (what
    ``mock-analytics/scripts/load_from_postgres.py`` produces in ``raw/``). Real
    seeded data, so the absolute numbers match the ones in the README.
  * otherwise, a deterministic synthetic seed generated from the baseline schema,
    so the simulation runs with no Docker, no Postgres and no dbt. The absolute
    numbers differ from the README's; the *ratios* — which are what the finding
    rests on — do not.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import sqlglot
from sqlglot import exp

from .impact import RenamePair, infer_renames
from .lineage import LineageIndex, ManifestGraph
from .schema_model import BaselineSchema, ChangeKind, SchemaChange

DEFAULT_ENUM_SHIFT = 0.10

# DuckDB types we can meaningfully SUM/AVG. Everything else is dimension, not metric.
_NUMERIC_TYPES = (
    "TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT",
    "UTINYINT", "USMALLINT", "UINTEGER", "UBIGINT",
    "FLOAT", "DOUBLE", "REAL", "DECIMAL", "NUMERIC",
)

# Rendered SQLAlchemy type -> DuckDB type. Order matters: the first hit wins, so
# the more specific patterns (BigInteger before Integer, DateTime before Date)
# have to come first.
_TYPE_PATTERNS: list[tuple[str, str]] = [
    (r"JSONB|JSON", "JSON"),
    (r"ENUM", "VARCHAR"),
    (r"UUID", "UUID"),
    (r"BigInteger|BIGINT", "BIGINT"),
    (r"SmallInteger|SMALLINT", "SMALLINT"),
    (r"Integer|INTEGER|\bINT\b", "INTEGER"),
    (r"Numeric|Decimal|DECIMAL", "DECIMAL"),
    (r"Float|Double|REAL", "DOUBLE"),
    (r"Boolean|BOOLEAN", "BOOLEAN"),
    (r"DateTime|TIMESTAMP", "TIMESTAMP"),
    (r"\bDate\b|\bDATE\b", "DATE"),
    (r"\bTime\b", "TIME"),
    (r"LargeBinary|BYTEA|BLOB", "BLOB"),
    (r"Text|Unicode|String|VARCHAR|CHAR", "VARCHAR"),
]

_PRECISION = re.compile(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)")
_DML = re.compile(r"^\s*(update|insert|delete)\b", re.IGNORECASE)


class SimulationUnavailable(RuntimeError):
    """Raised when the simulation cannot run (missing duckdb, unusable sources)."""


# --------------------------------------------------------------------------- #
# Result types
# --------------------------------------------------------------------------- #


@dataclass
class ColumnStats:
    total: float | None
    mean: float | None
    nulls: int


@dataclass
class ModelSnapshot:
    model: str
    row_count: int | None = None
    columns: dict[str, ColumnStats] = field(default_factory=dict)
    error: str | None = None  # the model failed to build

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class WarehouseSnapshot:
    models: dict[str, ModelSnapshot] = field(default_factory=dict)

    @property
    def failed(self) -> dict[str, str]:
        return {m: s.error for m, s in self.models.items() if s.error}


@dataclass
class MetricDelta:
    """One measurable difference between the baseline and the post-change build."""

    model: str
    metric: str  # "rows", "sum(col)", "avg(col)"
    before: float | None
    after: float | None
    scale: float | None = None  # clean power-of-ten rescale, e.g. 0.01

    @property
    def broke(self) -> bool:
        return self.after is None

    @property
    def ratio(self) -> float | None:
        if self.before in (None, 0) or self.after is None:
            return None
        return self.after / self.before

    @property
    def pct_change(self) -> float | None:
        r = self.ratio
        return None if r is None else (r - 1.0) * 100.0


@dataclass
class PatchRecord:
    model: str
    rename: str  # "amount_cents -> amount"


@dataclass
class EnumCounterfactual:
    enum_type: str
    value: str
    table: str
    column: str
    fraction: float
    rows_moved: int
    from_values: list[str]


@dataclass
class SimulationReport:
    source_mode: str
    source_rows: dict[str, int] = field(default_factory=dict)
    baseline: WarehouseSnapshot = field(default_factory=WarehouseSnapshot)
    candidate: WarehouseSnapshot = field(default_factory=WarehouseSnapshot)
    deltas: list[MetricDelta] = field(default_factory=list)
    as_is_failures: dict[str, str] = field(default_factory=dict)
    patches: list[PatchRecord] = field(default_factory=list)
    applied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    counterfactuals: list[EnumCounterfactual] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def changed_models(self) -> list[str]:
        out: list[str] = []
        for d in self.deltas:
            if d.model not in out:
                out.append(d.model)
        return out

    def deltas_for(self, model: str) -> list[MetricDelta]:
        return [d for d in self.deltas if d.model == model]

    def headlines(self) -> list[str]:
        """One human sentence per materially affected model."""
        lines: list[str] = []
        for model in self.changed_models:
            ds = self.deltas_for(model)
            if any(d.broke for d in ds):
                lines.append(f"{model}: fails to build after this change.")
                continue
            scaled = [d for d in ds if d.scale is not None and d.metric.startswith("avg(")]
            rows = next((d for d in ds if d.metric == "rows"), None)
            if scaled:
                factor = scaled[0].scale
                cols = ", ".join(d.metric[4:-1] for d in scaled)
                lines.append(
                    f"{model}: {cols} rescaled by x{factor:g} "
                    f"({_fmt(1 / factor)}x off) while still compiling — units changed."
                )
                continue

            biggest = biggest_mover(ds)
            if rows is not None and rows.before and rows.after is not None:
                lost = rows.before - rows.after
                tail = ""
                if biggest is not None:
                    tail = (
                        f"; {biggest.metric[4:-1]} "
                        f"{'falls' if biggest.pct_change < 0 else 'rises'} "
                        f"{abs(biggest.pct_change):.1f}%"
                    )
                lines.append(
                    f"{model}: {abs(lost):,.0f} row(s) "
                    f"{'dropped' if lost > 0 else 'added'} silently{tail}."
                )
            elif biggest is not None:
                lines.append(
                    f"{model}: same row count, but {biggest.metric[4:-1]} "
                    f"{'falls' if biggest.pct_change < 0 else 'rises'} "
                    f"{abs(biggest.pct_change):.1f}% — the shape of the data moved."
                )
            else:
                lines.append(f"{model}: {len(ds)} metric(s) changed.")
        return lines


def _fmt(x: float) -> str:
    return f"{x:g}"


def biggest_mover(deltas: list[MetricDelta]) -> MetricDelta | None:
    """The summed metric that moved most, in percentage terms — the one to quote."""
    sums = [
        d
        for d in deltas
        if d.metric.startswith("sum(") and d.pct_change not in (None, 0)
    ]
    return max(sums, key=lambda d: abs(d.pct_change), default=None)


# --------------------------------------------------------------------------- #
# DuckDB helpers
# --------------------------------------------------------------------------- #


def _connect():
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise SimulationUnavailable(
            "the simulation layer needs duckdb: pip install 'data-contract-agent[sim]'"
        ) from exc
    return duckdb.connect(":memory:")


def duckdb_type(rendered: str | None) -> str:
    """Map a rendered SQLAlchemy type (``sa.Numeric(12, 2)``) to a DuckDB type."""
    if not rendered:
        return "VARCHAR"
    for pattern, ddl in _TYPE_PATTERNS:
        if re.search(pattern, rendered):
            if ddl == "DECIMAL":
                m = _PRECISION.search(rendered)
                return f"DECIMAL({m.group(1)},{m.group(2)})" if m else "DECIMAL(18,4)"
            return ddl
    return "VARCHAR"


def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


# --------------------------------------------------------------------------- #
# Source loading
# --------------------------------------------------------------------------- #


def _find_parquet_dir(path: Path) -> Path | None:
    for candidate in (path, path / "raw"):
        if candidate.is_dir() and any(candidate.glob("*.parquet")):
            return candidate
    return None


def load_sources(
    con, schema: BaselineSchema, source_tables: set[str], sources: str | Path | None
) -> tuple[str, dict[str, int]]:
    """Populate the throwaway warehouse with the operational tables.

    Returns ``(mode, {table: row_count})``.
    """
    wanted = sorted(t for t in source_tables if t in schema.tables)
    if not wanted:
        raise SimulationUnavailable(
            "no source table in the dbt manifest matches the baseline migration's schema"
        )

    if sources:
        directory = _find_parquet_dir(Path(sources))
        if directory is None:
            raise SimulationUnavailable(
                f"no *.parquet found in {sources} (or {Path(sources) / 'raw'}). "
                "Run mock-analytics/scripts/load_from_postgres.py, or drop --sources "
                "to use the synthetic seed."
            )
        counts: dict[str, int] = {}
        for table in wanted:
            f = directory / f"{table}.parquet"
            if not f.exists():
                raise SimulationUnavailable(f"missing {f}")
            con.execute(
                f"CREATE TABLE {_q(table)} AS SELECT * FROM read_parquet(?)", [str(f)]
            )
            counts[table] = _count(con, table)
        return (f"parquet ({directory})", counts)

    counts = _seed_synthetic(con, schema, wanted)
    return ("synthetic", counts)


def _count(con, table: str) -> int:
    return int(con.execute(f"SELECT count(*) FROM {_q(table)}").fetchone()[0])


def _create_table(con, schema: BaselineSchema, table: str) -> list[str]:
    """CREATE TABLE straight from the baseline migration's column list."""
    tdef = schema.tables[table]
    cols = [f"{_q(c.name)} {duckdb_type(c.type)}" for c in tdef.columns.values()]
    con.execute(f"CREATE TABLE {_q(table)} ({', '.join(cols)})")
    return list(tdef.columns)


# Distributions kept in step with mock-app-service/docs/decision-log.md, so the
# synthetic seed has the same *shape* as scripts/seed.py, just smaller.
_PLAN_TIERS = [("free", 0.50), ("pro", 0.30), ("team", 0.15), ("enterprise", 0.05)]
_STATUSES = [("active", 0.65), ("trialing", 0.10), ("cancelled", 0.25)]
_TX_STATUSES = [("succeeded", 0.90), ("failed", 0.07), ("refunded", 0.03)]
_COUNTRIES = ["US", "GB", "DE", "IN", "CA", "AU", "BR", "JP"]
_EVENT_NAMES = ["login", "feature_used", "page_view", "export", "invite_sent"]
_PRICE_CENTS_SQL = (
    "CASE plan_tier WHEN 'pro' THEN 2900 WHEN 'team' THEN 9900 ELSE 49900 END"
)
_EPOCH_SQL = "TIMESTAMP '2024-01-01'"
_SLOTS = 20  # granularity of the weighted pickers below


def _sql_list(values: list[str]) -> str:
    return "[" + ", ".join("'" + v.replace("'", "''") + "'" for v in values) + "]"


def _weighted_list(weighted: list[tuple[str, float]]) -> str:
    """Expand [(value, weight)] into a fixed-length SQL list literal to sample from."""
    out: list[str] = []
    for value, weight in weighted:
        out.extend([value] * max(1, round(weight * _SLOTS)))
    return _sql_list((out + [weighted[-1][0]] * _SLOTS)[:_SLOTS])


def _pick_sql(list_literal: str, seed_expr: str, slots: int = _SLOTS) -> str:
    """Deterministically sample a SQL list literal. DuckDB lists are 1-indexed."""
    return f"({list_literal})[CAST(hash({seed_expr}) % {slots} AS BIGINT) + 1]"


def _days_sql(seed_expr: str, span: int) -> str:
    return f"{_EPOCH_SQL} + to_days(CAST(hash({seed_expr}) % {span} AS INTEGER))"


def _seed_synthetic(
    con, schema: BaselineSchema, tables: list[str], *, n_users: int = 400
) -> dict[str, int]:
    """Deterministic stand-in data so the simulation runs with zero setup.

    Generated set-based in SQL rather than row-by-row from Python: DuckDB's
    parameter binding costs ~20ms a row, so a few thousand seeded rows through
    ``executemany`` takes over a minute, while the equivalent ``INSERT ... SELECT``
    over ``range()`` is milliseconds. ``hash()`` stands in for the RNG, which keeps
    the whole seed reproducible run to run.

    The DDL still comes from the baseline migration, so a column added there shows
    up here automatically — just as NULL, since only the columns the analytics
    models actually read are given values.
    """
    counts: dict[str, int] = {}
    known = set(tables)
    n_accounts = max(1, int(n_users * 0.8))
    n_events = n_users * 12

    for table in tables:
        _create_table(con, schema, table)

    if "users" in known:
        con.execute(f"""
            INSERT INTO users (id, email, full_name, country, is_active, signup_date)
            SELECT i,
                   'user' || i || '@example.com',
                   'User ' || i,
                   {_pick_sql(_sql_list(_COUNTRIES), 'i * 7', len(_COUNTRIES))},
                   (hash(i * 11) % 10) <> 0,
                   {_days_sql('i * 13', 600)}
            FROM range(1, {n_users + 1}) t(i)
        """)
        counts["users"] = _count(con, "users")

    if "accounts" in known:
        con.execute(f"""
            INSERT INTO accounts (id, owner_user_id, name, plan_tier, created_at)
            SELECT i,
                   CAST(hash(i * 17) % {n_users} AS BIGINT) + 1,
                   'Account ' || i,
                   {_pick_sql(_weighted_list(_PLAN_TIERS), 'i * 19')},
                   {_days_sql('i * 23', 600)}
            FROM range(1, {n_accounts + 1}) t(i)
        """)
        counts["accounts"] = _count(con, "accounts")

    if "subscriptions" in known:
        # One subscription per paying account; free-tier accounts get none.
        con.execute(f"""
            INSERT INTO subscriptions (
                id, account_id, plan_name, amount_cents, currency,
                billing_interval, status, started_at, canceled_at)
            WITH paid AS (
                SELECT id AS account_id, plan_tier FROM accounts WHERE plan_tier <> 'free'
            ),
            priced AS (
                SELECT row_number() over (order by account_id)      AS id,
                       account_id,
                       plan_tier                                    AS plan_name,
                       CASE WHEN hash(account_id * 29) % 5 = 0
                            THEN 'yearly' ELSE 'monthly' END        AS billing_interval,
                       {_PRICE_CENTS_SQL}                           AS unit_cents,
                       {_pick_sql(_weighted_list(_STATUSES), 'account_id * 31')} AS status,
                       {_days_sql('account_id * 37', 600)}          AS started_at
                FROM paid
            )
            SELECT id, account_id, plan_name,
                   unit_cents * CASE WHEN billing_interval = 'yearly' THEN 10 ELSE 1 END,
                   'USD', billing_interval, status, started_at,
                   CASE WHEN status = 'cancelled'
                        THEN started_at + to_days(CAST(hash(id * 41) % 200 AS INTEGER) + 1)
                   END
            FROM priced
        """)
        counts["subscriptions"] = _count(con, "subscriptions")

    if "transactions" in known and "subscriptions" in known:
        con.execute(f"""
            INSERT INTO transactions (
                id, account_id, subscription_id, amount_cents, currency, status, occurred_at)
            SELECT row_number() over (order by s.id, k),
                   s.account_id, s.id, s.amount_cents, 'USD',
                   {_pick_sql(_weighted_list(_TX_STATUSES), 's.id * 43 + k')},
                   {_days_sql('s.id * 47 + k', 600)}
            FROM subscriptions s, range(1, 4) t(k)
        """)
        counts["transactions"] = _count(con, "transactions")

    if "events" in known:
        con.execute(f"""
            INSERT INTO events (id, user_id, account_id, event_name, occurred_at, properties)
            SELECT i,
                   CAST(hash(i * 53) % {n_users} AS BIGINT) + 1,
                   CAST(hash(i * 59) % {n_accounts} AS BIGINT) + 1,
                   {_pick_sql(_sql_list(_EVENT_NAMES), 'i * 61', len(_EVENT_NAMES))},
                   {_days_sql('i * 67', 600)},
                   '{{"source":"synthetic"}}'
            FROM range(1, {n_events + 1}) t(i)
        """)
        counts["events"] = _count(con, "events")

    for table in tables:
        counts.setdefault(table, _count(con, table))
    return counts


# --------------------------------------------------------------------------- #
# Replaying the migration onto the warehouse
# --------------------------------------------------------------------------- #


def apply_changes(
    con,
    changes: list[SchemaChange],
    schema: BaselineSchema,
    index: LineageIndex,
    source_tables: set[str],
    *,
    enum_shift: float = DEFAULT_ENUM_SHIFT,
) -> tuple[list[str], list[str], list[EnumCounterfactual]]:
    """Replay the parsed migration against the throwaway warehouse.

    Applied in migration order, because order is load-bearing: add-then-backfill-
    then-drop only works if the drop happens last.

    Returns ``(applied_sql, skipped_notes, counterfactuals)``.
    """
    applied: list[str] = []
    skipped: list[str] = []
    counterfactuals: list[EnumCounterfactual] = []

    def run(sql: str, params: list | None = None) -> bool:
        try:
            con.execute(sql, params or [])
        except Exception as exc:  # noqa: BLE001 - a failed replay is a note, not a crash
            skipped.append(f"{sql.strip()[:90]} -> {type(exc).__name__}: {exc}")
            return False
        applied.append(sql.strip())
        return True

    for ch in changes:
        if ch.table and ch.table not in source_tables:
            skipped.append(
                f"{ch.describe()} (table '{ch.table}' is not a dbt source; nothing to simulate)"
            )
            continue

        if ch.kind is ChangeKind.RENAME_COLUMN:
            run(
                f"ALTER TABLE {_q(ch.table)} RENAME COLUMN "
                f"{_q(ch.column)} TO {_q(ch.new_column)}"
            )

        elif ch.kind is ChangeKind.ADD_COLUMN:
            run(
                f"ALTER TABLE {_q(ch.table)} ADD COLUMN "
                f"{_q(ch.column)} {duckdb_type(ch.new_type)}"
            )

        elif ch.kind is ChangeKind.DROP_COLUMN:
            run(f"ALTER TABLE {_q(ch.table)} DROP COLUMN {_q(ch.column)}")

        elif ch.kind is ChangeKind.ALTER_TYPE:
            run(
                f"ALTER TABLE {_q(ch.table)} ALTER COLUMN {_q(ch.column)} "
                f"TYPE {duckdb_type(ch.new_type)}"
            )

        elif ch.kind is ChangeKind.ALTER_NULLABILITY:
            # Constraints don't move numbers; the metric diff is unaffected.
            skipped.append(f"{ch.describe()} (constraint only, no metric effect)")

        elif ch.kind is ChangeKind.ENUM_ADD_VALUE:
            cf = _enum_counterfactual(con, ch, schema, index, source_tables, enum_shift)
            if cf:
                counterfactuals.extend(cf)
            else:
                skipped.append(
                    f"{ch.describe()} (no source column uses this enum; nothing to project)"
                )

        elif ch.kind is ChangeKind.RAW_SQL:
            sql = (ch.raw_sql or "").strip()
            if _DML.match(sql):
                run(sql)
            else:
                skipped.append(f"raw SQL not replayed (not DML): {sql[:80]}")

    return applied, skipped, counterfactuals


def _enum_counterfactual(
    con,
    ch: SchemaChange,
    schema: BaselineSchema,
    index: LineageIndex,
    source_tables: set[str],
    fraction: float,
) -> list[EnumCounterfactual]:
    """Project the damage from a new enum value that no row carries yet.

    ``ALTER TYPE ... ADD VALUE`` is inert on the day it merges. What matters is
    what happens once the application writes the value — so move a fraction of the
    rows a downstream filter currently *accepts* into the new value and measure.
    Explicitly a projection, and reported as one.
    """
    out: list[EnumCounterfactual] = []
    targets = [
        (t, c) for t, c in schema.columns_for_enum(ch.enum_type) if t in source_tables
    ]

    for table, column in targets:
        covered = _covered_values(index, table, column)
        where = f"{_q(column)} <> ?"
        params: list[Any] = [ch.enum_value]
        if covered:
            placeholders = ", ".join("?" for _ in covered)
            where = f"{_q(column)} IN ({placeholders})"
            params = list(covered)

        eligible = int(
            con.execute(
                f"SELECT count(*) FROM {_q(table)} WHERE {where}", params
            ).fetchone()[0]
        )
        moved = int(round(eligible * fraction))
        if moved <= 0:
            continue

        # hash(rowid) keeps the sample pseudo-random but reproducible run to run.
        con.execute(
            f"UPDATE {_q(table)} SET {_q(column)} = ? WHERE rowid IN ("
            f"  SELECT rowid FROM {_q(table)} WHERE {where} "
            f"  ORDER BY hash(rowid) LIMIT {moved})",
            [ch.enum_value, *params],
        )
        out.append(
            EnumCounterfactual(
                enum_type=ch.enum_type,
                value=ch.enum_value,
                table=table,
                column=column,
                fraction=fraction,
                rows_moved=moved,
                from_values=sorted(covered),
            )
        )
    return out


def _covered_values(index: LineageIndex, table: str, column: str) -> set[str]:
    """The literal values downstream IN-filters currently accept for this column."""
    covered: set[str] = set()
    for filters in index.enum_filters_by_model.values():
        for f in filters:
            if (f.source_table, f.source_column) == (table, column):
                covered.update(f.values)
    return covered


# --------------------------------------------------------------------------- #
# Building the dbt DAG inside DuckDB
# --------------------------------------------------------------------------- #


def rename_columns_in_sql(sql: str, renames: dict[str, str]) -> tuple[str, bool]:
    """Apply ``old -> new`` to column *references* only.

    Parsed with sqlglot so comments and string literals can't be clobbered; falls
    back to a word-boundary substitution if the SQL doesn't parse.
    """
    try:
        tree = sqlglot.parse_one(sql, dialect="duckdb")
    except Exception:  # noqa: BLE001
        tree = None

    if tree is None:
        patched = sql
        for old, new in renames.items():
            patched = re.sub(rf"\b{re.escape(old)}\b", new, patched)
        return patched, patched != sql

    changed = False
    for col in tree.find_all(exp.Column):
        new = renames.get(col.name)
        if new:
            col.set("this", exp.to_identifier(new))
            changed = True
    return (tree.sql(dialect="duckdb", pretty=True), changed) if changed else (sql, False)


def build_models(
    con, graph: ManifestGraph, order: list[str], patched_sql: dict[str, str] | None = None
) -> dict[str, str]:
    """Materialize every model as a table, sources-first. Returns model -> error.

    Everything is built as a TABLE (not a view) so a model that references a
    dropped column fails *here*, where we can attribute the failure, rather than
    later during profiling.
    """
    patched_sql = patched_sql or {}
    name_to_id = {v: k for k, v in graph.model_name_by_id.items()}
    errors: dict[str, str] = {}

    for model in order:
        node = graph.models[name_to_id[model]]
        deps = [
            graph.model_name_by_id[d]
            for d in node.get("depends_on", {}).get("nodes", [])
            if d in graph.models
        ]
        blocked = [d for d in deps if d in errors]
        if blocked:
            errors[model] = f"blocked by upstream failure in {', '.join(blocked)}"
            continue

        sql = patched_sql.get(model)
        if sql is None:
            sql = graph.normalize_sql(
                node.get("compiled_code") or node.get("raw_code") or ""
            )
        try:
            con.execute(f"CREATE OR REPLACE TABLE {_q(model)} AS {sql}")
        except Exception as exc:  # noqa: BLE001 - a build failure IS the finding
            errors[model] = f"{type(exc).__name__}: {_first_line(exc)}"

    return errors


def _first_line(exc: Exception) -> str:
    return str(exc).strip().splitlines()[0][:200]


def drop_models(con, models: list[str]) -> None:
    for m in models:
        con.execute(f"DROP TABLE IF EXISTS {_q(m)}")


# --------------------------------------------------------------------------- #
# Profiling and diffing
# --------------------------------------------------------------------------- #


def _is_metric_column(name: str, dtype: str) -> bool:
    if name == "id" or name.endswith("_id"):
        return False  # surrogate keys aren't metrics; summing them is noise
    return dtype.upper().startswith(_NUMERIC_TYPES)


def snapshot(con, models: list[str], errors: dict[str, str]) -> WarehouseSnapshot:
    snap = WarehouseSnapshot()
    for model in models:
        if model in errors:
            snap.models[model] = ModelSnapshot(model=model, error=errors[model])
            continue

        described = con.execute(f"DESCRIBE {_q(model)}").fetchall()
        metric_cols = [r[0] for r in described if _is_metric_column(r[0], r[1])]

        selects = ["count(*)"]
        for c in metric_cols:
            selects += [
                f"sum(CAST({_q(c)} AS DOUBLE))",
                f"avg(CAST({_q(c)} AS DOUBLE))",
                f"count(*) - count({_q(c)})",
            ]
        row = con.execute(f"SELECT {', '.join(selects)} FROM {_q(model)}").fetchone()

        ms = ModelSnapshot(model=model, row_count=int(row[0]))
        for i, c in enumerate(metric_cols):
            total, mean, nulls = row[1 + i * 3], row[2 + i * 3], row[3 + i * 3]
            ms.columns[c] = ColumnStats(
                total=None if total is None else float(total),
                mean=None if mean is None else float(mean),
                nulls=int(nulls or 0),
            )
        snap.models[model] = ms
    return snap


def _scale_factor(before: float | None, after: float | None) -> float | None:
    """Return 10**n when after/before is a clean power of ten (n != 0)."""
    if not before or after is None or after <= 0 or before <= 0:
        return None
    exponent = math.log10(after / before)
    nearest = round(exponent)
    if nearest != 0 and abs(exponent - nearest) < 1e-6:
        return 10.0**nearest
    return None


def _differs(a: float | None, b: float | None, tol: float = 1e-9) -> bool:
    if a is None and b is None:
        return False
    if a is None or b is None:
        return True
    scale = max(abs(a), abs(b), 1.0)
    return abs(a - b) > tol * scale


def diff(before: WarehouseSnapshot, after: WarehouseSnapshot) -> list[MetricDelta]:
    deltas: list[MetricDelta] = []
    for model, base in before.models.items():
        cand = after.models.get(model)
        if cand is None:
            continue
        if not base.ok:
            continue  # it was already broken; nothing to attribute to this change
        if not cand.ok:
            deltas.append(
                MetricDelta(model=model, metric="rows", before=base.row_count, after=None)
            )
            continue

        if base.row_count != cand.row_count:
            deltas.append(
                MetricDelta(
                    model=model,
                    metric="rows",
                    before=float(base.row_count or 0),
                    after=float(cand.row_count or 0),
                )
            )

        for col, bstats in base.columns.items():
            cstats = cand.columns.get(col)
            if cstats is None:
                deltas.append(
                    MetricDelta(model=model, metric=f"sum({col})", before=bstats.total, after=None)
                )
                continue
            if _differs(bstats.total, cstats.total):
                deltas.append(
                    MetricDelta(
                        model=model,
                        metric=f"sum({col})",
                        before=bstats.total,
                        after=cstats.total,
                        scale=_scale_factor(bstats.total, cstats.total),
                    )
                )
            if _differs(bstats.mean, cstats.mean):
                deltas.append(
                    MetricDelta(
                        model=model,
                        metric=f"avg({col})",
                        before=bstats.mean,
                        after=cstats.mean,
                        scale=_scale_factor(bstats.mean, cstats.mean),
                    )
                )
    return deltas


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def _patch_map(
    renames: list[RenamePair], graph: ManifestGraph, index: LineageIndex
) -> tuple[dict[str, str], list[PatchRecord]]:
    """The mechanical fix a reviewer would apply, scoped to the models that need it.

    Scoped deliberately: ``subscriptions.amount_cents`` and
    ``transactions.amount_cents`` are different columns that happen to share a
    name, so a repo-wide find-replace would corrupt ``stg_transactions``. Only
    models whose *lineage* reads the renamed source column get patched.
    """
    per_model: dict[str, dict[str, str]] = {}
    for pair in renames:
        for model in index.models_reading(pair.table, pair.old_column):
            per_model.setdefault(model, {})[pair.old_column] = pair.new_column

    name_to_id = {v: k for k, v in graph.model_name_by_id.items()}
    patched: dict[str, str] = {}
    records: list[PatchRecord] = []
    for model, renames_for_model in per_model.items():
        if model not in name_to_id:
            continue
        node = graph.models[name_to_id[model]]
        sql = graph.normalize_sql(node.get("compiled_code") or node.get("raw_code") or "")
        new_sql, changed = rename_columns_in_sql(sql, renames_for_model)
        if not changed:
            continue  # the model reads the column transitively, not by name
        patched[model] = new_sql
        records.extend(
            PatchRecord(model=model, rename=f"{old} -> {new}")
            for old, new in renames_for_model.items()
        )
    return patched, records


def simulate(
    changes: list[SchemaChange],
    manifest_path: str | Path,
    schema: BaselineSchema,
    index: LineageIndex,
    *,
    sources: str | Path | None = None,
    enum_shift: float = DEFAULT_ENUM_SHIFT,
    auto_patch: bool = True,
) -> SimulationReport:
    """Build the marts before and after the migration, and diff the numbers."""
    import json

    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    graph = ManifestGraph(manifest)
    order = graph.topo_models()
    source_tables = set(graph.source_names)

    con = _connect()
    try:
        mode, counts = load_sources(con, schema, source_tables, sources)

        baseline_errors = build_models(con, graph, order)
        baseline = snapshot(con, order, baseline_errors)
        report = SimulationReport(source_mode=mode, source_rows=counts, baseline=baseline)
        if baseline_errors:
            report.notes.append(
                "baseline build already failing for: " + ", ".join(sorted(baseline_errors))
            )

        applied, skipped, cfs = apply_changes(
            con, changes, schema, index, source_tables, enum_shift=enum_shift
        )
        report.applied, report.skipped, report.counterfactuals = applied, skipped, cfs

        # Pass 1: the loud half — what simply stops compiling.
        drop_models(con, order)
        as_is_errors = build_models(con, graph, order)
        report.as_is_failures = {
            m: e for m, e in as_is_errors.items() if m not in baseline_errors
        }

        # Pass 2: the quiet half — rebuild with the mechanical rename applied.
        errors, snap = as_is_errors, None
        if auto_patch:
            patched_sql, records = _patch_map(infer_renames(changes), graph, index)
            if patched_sql:
                report.patches = records
                drop_models(con, order)
                errors = build_models(con, graph, order, patched_sql=patched_sql)
                snap = snapshot(con, order, errors)

        if snap is None:
            snap = snapshot(con, order, errors)

        report.candidate = snap
        report.deltas = diff(baseline, snap)
        return report
    finally:
        con.close()
