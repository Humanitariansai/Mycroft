from conftest import MIGRATIONS

from contract_agent.impact import (
    ENUM_REVIEW,
    SEMANTIC_REVIEW,
    STRUCTURAL_BREAK,
    analyze,
)
from contract_agent.migration_parser import parse_migration


def _report(name, index, schema):
    changes = parse_migration(MIGRATIONS / name)
    return analyze(name, changes, index, schema)


def test_scenario1_is_structural_break(index, schema):
    r = _report("0002_rename_signup_date.py", index, schema)
    breaks = r.by_category(STRUCTURAL_BREAK)
    assert len(breaks) == 1
    assert breaks[0].deterministic is True
    assert set(breaks[0].affected_models) == {"stg_users", "dim_users", "fct_engagement"}


def test_scenario2_has_structural_and_semantic(index, schema):
    r = _report("0003_subscriptions_amount.py", index, schema)
    # the dropped column is a provable structural break
    assert any(
        set(f.affected_models) == {"stg_subscriptions", "fct_mrr"}
        for f in r.by_category(STRUCTURAL_BREAK)
    )
    # and the unit change is surfaced for the semantic layer
    sem = r.by_category(SEMANTIC_REVIEW)
    assert sem and sem[0].deterministic is False
    assert "cents" in sem[0].summary.lower() or "unit" in sem[0].summary.lower()


def test_scenario3_is_enum_review_flagging_uncovered_value(index, schema):
    r = _report("0004_subscription_status_paused.py", index, schema)
    enum = r.by_category(ENUM_REVIEW)
    assert len(enum) == 1
    assert enum[0].deterministic is False
    assert "paused" in enum[0].summary
    assert "fct_mrr" in enum[0].affected_models


def test_control_migration_has_no_impact(index, schema):
    r = _report("0005_add_user_phone.py", index, schema)
    assert r.by_category(STRUCTURAL_BREAK) == []
    assert r.by_category(SEMANTIC_REVIEW) == []
    assert r.by_category(ENUM_REVIEW) == []
    assert r.affected_models == []
