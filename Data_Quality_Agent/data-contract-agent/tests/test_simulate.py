"""Tests for the metric-level impact simulation.

These assert on *ratios*, not absolute values, so they hold against the synthetic
seed here and against the real Postgres-seeded parquet a developer would point
``--sources`` at.
"""
import pytest
from conftest import MANIFEST, MIGRATIONS

from contract_agent.impact import infer_renames
from contract_agent.migration_parser import parse_migration
from contract_agent.simulate import (
    duckdb_type,
    rename_columns_in_sql,
    simulate,
)

pytest.importorskip("duckdb", reason="the simulation layer needs the [sim] extra")


@pytest.fixture(scope="module")
def run(schema, index):
    cache: dict[str, object] = {}

    def _run(migration: str, **kwargs):
        key = migration + repr(sorted(kwargs.items()))
        if key not in cache:
            cache[key] = simulate(
                parse_migration(MIGRATIONS / migration), MANIFEST, schema, index, **kwargs
            )
        return cache[key]

    return _run


def _delta(report, model, metric):
    return next((d for d in report.deltas if d.model == model and d.metric == metric), None)


# --------------------------------------------------------------------------- #
# Scenario 2 — the headline: compiles clean, 100x wrong
# --------------------------------------------------------------------------- #


def test_scenario2_breaks_loudly_before_the_mechanical_fix(run):
    r = run("0003_subscriptions_amount.py")
    assert "stg_subscriptions" in r.as_is_failures
    assert "amount_cents" in r.as_is_failures["stg_subscriptions"]
    assert r.as_is_failures["fct_mrr"].startswith("blocked by upstream")


def test_scenario2_mrr_is_100x_low_after_the_mechanical_fix(run):
    r = run("0003_subscriptions_amount.py")
    assert [(p.model, p.rename) for p in r.patches] == [
        ("stg_subscriptions", "amount_cents -> amount")
    ]
    # nothing fails to build once the rename is applied -- that's the whole danger
    assert r.candidate.failed == {}

    mrr = _delta(r, "fct_mrr", "sum(monthly_amount_usd)")
    assert mrr is not None, "fct_mrr's headline metric should have moved"
    assert mrr.scale == pytest.approx(0.01)
    assert mrr.after == pytest.approx(mrr.before / 100.0)


def test_scenario2_row_count_is_unchanged(run):
    """The rows are all still there. Only their magnitude is wrong -- that's why
    row-count monitoring and dbt tests both miss this."""
    r = run("0003_subscriptions_amount.py")
    assert _delta(r, "fct_mrr", "rows") is None
    assert r.baseline.models["fct_mrr"].row_count == r.candidate.models["fct_mrr"].row_count


def test_scenario2_leaves_unrelated_marts_alone(run):
    """transactions.amount_cents shares a name with the renamed column but is a
    different column, so fct_revenue must not be touched."""
    r = run("0003_subscriptions_amount.py")
    assert "fct_revenue" not in r.changed_models
    assert "fct_revenue" not in {p.model for p in r.patches}


def test_scenario2_headline_names_the_unit_change(run):
    joined = " ".join(run("0003_subscriptions_amount.py").headlines())
    assert "fct_mrr" in joined
    assert "units changed" in joined


# --------------------------------------------------------------------------- #
# Scenario 1 — loud, but harmless once fixed
# --------------------------------------------------------------------------- #


def test_scenario1_breaks_three_models_then_recovers_cleanly(run):
    r = run("0002_rename_signup_date.py")
    assert set(r.as_is_failures) == {"stg_users", "dim_users", "fct_engagement"}
    assert [(p.model, p.rename) for p in r.patches] == [
        ("stg_users", "signup_date -> created_at")
    ]
    assert r.candidate.failed == {}
    assert r.deltas == [], "a pure rename must not move a single number"


def test_scenario1_without_auto_patch_reports_the_break(run):
    r = run("0002_rename_signup_date.py", auto_patch=False)
    broke = {d.model for d in r.deltas if d.broke}
    assert {"stg_users", "dim_users", "fct_engagement"} <= broke


# --------------------------------------------------------------------------- #
# Scenario 3 — the enum counterfactual
# --------------------------------------------------------------------------- #


def test_scenario3_projects_rows_out_of_mrr(run):
    r = run("0004_subscription_status_paused.py")
    assert r.as_is_failures == {}, "an enum addition compiles fine; that's the problem"

    (cf,) = r.counterfactuals
    assert (cf.table, cf.column, cf.value) == ("subscriptions", "status", "paused")
    assert cf.from_values == ["active", "trialing"], "must move rows the filter accepts"
    assert cf.rows_moved > 0

    rows = _delta(r, "fct_mrr", "rows")
    assert rows is not None and rows.after < rows.before
    assert rows.before - rows.after == pytest.approx(cf.rows_moved)
    assert _delta(r, "fct_mrr", "sum(monthly_amount_usd)").pct_change < 0


def test_scenario3_shift_size_scales_the_projection(run):
    small = run("0004_subscription_status_paused.py", enum_shift=0.05)
    large = run("0004_subscription_status_paused.py", enum_shift=0.40)
    assert small.counterfactuals[0].rows_moved < large.counterfactuals[0].rows_moved
    assert _delta(large, "fct_mrr", "rows").after < _delta(small, "fct_mrr", "rows").after


def test_zero_shift_is_a_no_op(run):
    r = run("0004_subscription_status_paused.py", enum_shift=0.0)
    assert r.counterfactuals == []
    assert r.deltas == []


# --------------------------------------------------------------------------- #
# Control
# --------------------------------------------------------------------------- #


def test_control_migration_moves_nothing(run):
    r = run("0005_add_user_phone.py")
    assert r.as_is_failures == {}
    assert r.deltas == []
    assert r.headlines() == []


def test_baseline_warehouse_builds_every_model(run):
    r = run("0005_add_user_phone.py")
    assert r.baseline.failed == {}
    assert {"stg_users", "stg_subscriptions", "fct_mrr", "fct_revenue"} <= set(
        r.baseline.models
    )
    assert r.baseline.models["fct_mrr"].row_count > 0


def test_simulation_is_deterministic(schema, index):
    """Same inputs, same numbers -- the seed uses hash(), not an RNG with state."""
    a, b = (
        simulate(
            parse_migration(MIGRATIONS / "0003_subscriptions_amount.py"),
            MANIFEST,
            schema,
            index,
        )
        for _ in range(2)
    )
    assert [(d.model, d.metric, d.before, d.after) for d in a.deltas] == [
        (d.model, d.metric, d.before, d.after) for d in b.deltas
    ]


def test_parquet_sources_produce_the_same_verdict(tmp_path, schema, index):
    """The --sources path (real seeded data) must behave like the synthetic seed.

    Exercised by round-tripping the synthetic seed through Parquet, which is the
    same shape `mock-analytics/scripts/load_from_postgres.py` writes to raw/.
    """
    from contract_agent.simulate import _connect, load_sources

    con = _connect()
    tables = ["users", "accounts", "subscriptions", "transactions", "events"]
    load_sources(con, schema, set(tables), None)
    raw = tmp_path / "raw"
    raw.mkdir()
    for table in tables:
        con.execute(f"COPY {table} TO '{(raw / f'{table}.parquet').as_posix()}' (FORMAT PARQUET)")
    con.close()

    r = simulate(
        parse_migration(MIGRATIONS / "0003_subscriptions_amount.py"),
        MANIFEST,
        schema,
        index,
        sources=tmp_path,  # resolves tmp_path/raw, like pointing at mock-analytics/
    )
    assert r.source_mode.startswith("parquet")
    assert r.source_rows["users"] == 400
    assert _delta(r, "fct_mrr", "sum(monthly_amount_usd)").scale == pytest.approx(0.01)


def test_unusable_sources_raise_rather_than_silently_falling_back(tmp_path, schema, index):
    from contract_agent.simulate import SimulationUnavailable

    with pytest.raises(SimulationUnavailable, match="no \\*.parquet found"):
        simulate(
            parse_migration(MIGRATIONS / "0005_add_user_phone.py"),
            MANIFEST,
            schema,
            index,
            sources=tmp_path,
        )


# --------------------------------------------------------------------------- #
# Units
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("rendered", "expected"),
    [
        ("sa.BigInteger()", "BIGINT"),
        ("sa.Integer()", "INTEGER"),
        ("sa.Numeric(12, 2)", "DECIMAL(12,2)"),
        ("sa.String(length=320)", "VARCHAR"),
        ("sa.Boolean()", "BOOLEAN"),
        ("sa.DateTime(timezone=True)", "TIMESTAMP"),
        ("postgresql.JSONB()", "JSON"),
        ("postgresql.ENUM('active', name='subscription_status')", "VARCHAR"),
        (None, "VARCHAR"),
    ],
)
def test_duckdb_type_mapping(rendered, expected):
    assert duckdb_type(rendered) == expected


def test_rename_only_touches_column_references():
    sql = (
        "-- amount_cents is in cents here\n"
        "select id, amount_cents / 100.0 as amount_usd, 'amount_cents' as label "
        "from subscriptions"
    )
    patched, changed = rename_columns_in_sql(sql, {"amount_cents": "amount"})
    assert changed
    assert "amount / 100.0" in patched
    assert "'amount_cents'" in patched, "string literals must survive untouched"


def test_rename_reports_no_change_when_column_is_absent():
    sql = "select user_id, signup_at from stg_users"
    patched, changed = rename_columns_in_sql(sql, {"signup_date": "created_at"})
    assert (patched, changed) == (sql, False)


def test_infer_renames_covers_both_forms():
    explicit = infer_renames(parse_migration(MIGRATIONS / "0002_rename_signup_date.py"))
    assert [(p.old_column, p.new_column, p.explicit) for p in explicit] == [
        ("signup_date", "created_at", True)
    ]

    disguised = infer_renames(
        parse_migration(MIGRATIONS / "0003_subscriptions_amount.py")
    )
    assert len(disguised) == 1
    assert (disguised[0].old_column, disguised[0].new_column) == ("amount_cents", "amount")
    assert disguised[0].explicit is False
    assert disguised[0].arithmetic is True, "the /100 backfill is the unit-change tell"
