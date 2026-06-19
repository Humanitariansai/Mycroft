from conftest import BASELINE, MIGRATIONS

from contract_agent.migration_parser import load_baseline_schema, parse_migration
from contract_agent.schema_model import ChangeKind


def test_baseline_schema_tables_and_columns():
    schema = load_baseline_schema(BASELINE)
    assert set(schema.tables) == {
        "users",
        "accounts",
        "subscriptions",
        "transactions",
        "events",
    }
    assert "signup_date" in schema.tables["users"].columns
    assert "amount_cents" in schema.tables["subscriptions"].columns


def test_baseline_detects_enum_backing():
    schema = load_baseline_schema(BASELINE)
    assert schema.column("subscriptions", "status").enum_type == "subscription_status"
    assert schema.columns_for_enum("subscription_status") == [("subscriptions", "status")]


def test_scenario1_rename():
    (c,) = parse_migration(MIGRATIONS / "0002_rename_signup_date.py")
    assert c.kind is ChangeKind.RENAME_COLUMN
    assert (c.table, c.column, c.new_column) == ("users", "signup_date", "created_at")


def test_scenario2_add_backfill_drop():
    changes = parse_migration(MIGRATIONS / "0003_subscriptions_amount.py")
    kinds = [c.kind for c in changes]
    assert ChangeKind.ADD_COLUMN in kinds
    assert ChangeKind.DROP_COLUMN in kinds
    assert ChangeKind.RAW_SQL in kinds
    backfill = next(c for c in changes if c.kind is ChangeKind.RAW_SQL)
    assert "amount_cents / 100.0" in backfill.raw_sql
    drop = next(c for c in changes if c.kind is ChangeKind.DROP_COLUMN)
    assert drop.column == "amount_cents"


def test_scenario3_enum_add_value():
    (c,) = parse_migration(MIGRATIONS / "0004_subscription_status_paused.py")
    assert c.kind is ChangeKind.ENUM_ADD_VALUE
    assert (c.enum_type, c.enum_value) == ("subscription_status", "paused")
