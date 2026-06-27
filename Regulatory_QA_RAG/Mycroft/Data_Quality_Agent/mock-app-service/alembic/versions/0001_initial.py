"""initial schema: users, accounts, subscriptions, transactions, events

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-21

Baseline schema for mock-app-service. The three "trap" columns are deliberate:

  - users.signup_date           (Scenario 1 renames to created_at)
  - subscriptions.amount_cents  (Scenario 2 renames to amount, switches to NUMERIC)
  - subscription_status enum    (Scenario 3 adds 'paused' via ALTER TYPE)

Subsequent scenario migrations live as separate revisions on feature branches.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    subscription_status = postgresql.ENUM(
        "active", "trialing", "cancelled", name="subscription_status"
    )
    subscription_status.create(op.get_bind(), checkfirst=True)

    billing_interval = postgresql.ENUM("monthly", "yearly", name="billing_interval")
    billing_interval.create(op.get_bind(), checkfirst=True)

    transaction_status = postgresql.ENUM(
        "succeeded", "failed", "refunded", name="transaction_status"
    )
    transaction_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=200)),
        sa.Column("country", sa.String(length=2)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "signup_date",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_country", "users", ["country"])

    op.create_table(
        "accounts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "owner_user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "plan_tier", sa.String(length=20), nullable=False, server_default=sa.text("'free'")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_accounts_owner_user_id", "accounts", ["owner_user_id"])
    op.create_index("ix_accounts_plan_tier", "accounts", ["plan_tier"])

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "account_id",
            sa.BigInteger(),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("plan_name", sa.String(length=50), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), nullable=False, server_default=sa.text("'USD'")
        ),
        sa.Column(
            "billing_interval",
            postgresql.ENUM(
                "monthly", "yearly", name="billing_interval", create_type=False
            ),
            nullable=False,
            server_default=sa.text("'monthly'"),
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active",
                "trialing",
                "cancelled",
                name="subscription_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("canceled_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_subscriptions_account_id", "subscriptions", ["account_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "account_id",
            sa.BigInteger(),
            sa.ForeignKey("accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            sa.BigInteger(),
            sa.ForeignKey("subscriptions.id", ondelete="SET NULL"),
        ),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), nullable=False, server_default=sa.text("'USD'")
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "succeeded",
                "failed",
                "refunded",
                name="transaction_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_index("ix_transactions_subscription_id", "transactions", ["subscription_id"])
    op.create_index("ix_transactions_status", "transactions", ["status"])
    op.create_index("ix_transactions_occurred_at", "transactions", ["occurred_at"])

    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column(
            "account_id",
            sa.BigInteger(),
            sa.ForeignKey("accounts.id", ondelete="SET NULL"),
        ),
        sa.Column("event_name", sa.String(length=80), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("properties", postgresql.JSONB()),
    )
    op.create_index("ix_events_user_id", "events", ["user_id"])
    op.create_index("ix_events_account_id", "events", ["account_id"])
    op.create_index("ix_events_event_name", "events", ["event_name"])
    op.create_index("ix_events_occurred_at", "events", ["occurred_at"])


def downgrade() -> None:
    op.drop_table("events")
    op.drop_table("transactions")
    op.drop_table("subscriptions")
    op.drop_table("accounts")
    op.drop_table("users")

    postgresql.ENUM(name="transaction_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="subscription_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="billing_interval").drop(op.get_bind(), checkfirst=True)
