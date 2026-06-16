import os

import pytest
from conftest import BASELINE, MANIFEST, MIGRATIONS

from contract_agent.impact import analyze
from contract_agent.migration_parser import load_baseline_schema, parse_migration
from contract_agent.semantic import (
    PRContext,
    RiskCategory,
    SemanticVerdict,
    analyze_semantic,
    build_user_prompt,
    model_sql_map,
)

FIXTURES = MIGRATIONS.parent
PRS = FIXTURES / "prs"


def _report(name):
    schema = load_baseline_schema(BASELINE)
    changes = parse_migration(MIGRATIONS / name)
    from contract_agent.lineage import build_lineage

    index = build_lineage(MANIFEST, schema)
    return analyze(name, changes, index, schema), schema


# ---- offline unit tests (no API key needed) -------------------------------


def test_model_sql_map_has_compiled_sql():
    sql = model_sql_map(MANIFEST)
    assert "fct_mrr" in sql
    assert "subscription_status" in sql["fct_mrr"]


def test_pr_context_from_files():
    pr = PRContext.from_files(PRS / "0003_subscriptions_amount.json", MIGRATIONS)
    assert "Standardize amount" in pr.title
    assert "amount_cents" in pr.migration_code


def test_user_prompt_assembles_all_context():
    report, schema = _report("0003_subscriptions_amount.py")
    pr = PRContext.from_files(PRS / "0003_subscriptions_amount.json", MIGRATIONS)
    prompt = build_user_prompt(pr, report, schema, model_sql_map(MANIFEST))
    # PR intent, migration backfill, deterministic finding, and downstream SQL all present
    assert "Standardize amount column" in prompt
    assert "amount_cents / 100.0" in prompt
    assert "fct_mrr" in prompt
    assert "subscriptions.amount_cents" in prompt  # column dictionary


def test_verdict_schema_validates():
    v = SemanticVerdict(
        contains_semantic_break=True,
        risk_category=RiskCategory.unit_change,
        affected_models=["fct_mrr"],
        reasoning="x",
        confidence=0.9,
    )
    assert v.risk_category is RiskCategory.unit_change


# ---- live tests (require ANTHROPIC_API_KEY; skipped otherwise) -------------

live = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set; skipping live LLM tests",
)


@live
def test_scenario2_flagged_as_unit_change():
    report, schema = _report("0003_subscriptions_amount.py")
    pr = PRContext.from_files(PRS / "0003_subscriptions_amount.json", MIGRATIONS)
    v = analyze_semantic(pr, report, schema, model_sql_map(MANIFEST))
    assert v.contains_semantic_break is True
    assert v.risk_category is RiskCategory.unit_change
    assert "fct_mrr" in v.affected_models


@live
def test_scenario1_not_a_semantic_break():
    report, schema = _report("0002_rename_signup_date.py")
    pr = PRContext.from_files(PRS / "0002_rename_signup_date.json", MIGRATIONS)
    v = analyze_semantic(pr, report, schema, model_sql_map(MANIFEST))
    assert v.contains_semantic_break is False


@live
def test_control_not_a_semantic_break():
    report, schema = _report("0005_add_user_phone.py")
    pr = PRContext.from_files(PRS / "0005_add_user_phone.json", MIGRATIONS)
    v = analyze_semantic(pr, report, schema, model_sql_map(MANIFEST))
    assert v.contains_semantic_break is False
