"""standardize subscriptions.amount column

Revision ID: 0003_subscriptions_amount
Revises: 0001_initial
"""
import sqlalchemy as sa
from alembic import op

revision = "0003_subscriptions_amount"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
    )
    op.execute("UPDATE subscriptions SET amount = amount_cents / 100.0")
    op.alter_column("subscriptions", "amount", nullable=False)
    op.drop_column("subscriptions", "amount_cents")


def downgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("amount_cents", sa.BigInteger(), nullable=True),
    )
    op.execute("UPDATE subscriptions SET amount_cents = (amount * 100)::bigint")
    op.alter_column("subscriptions", "amount_cents", nullable=False)
    op.drop_column("subscriptions", "amount")
