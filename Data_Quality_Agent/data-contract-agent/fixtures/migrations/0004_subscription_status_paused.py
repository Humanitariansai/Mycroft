"""add paused to subscription_status

Revision ID: 0004_subscription_status_paused
Revises: 0001_initial
"""
from alembic import op

revision = "0004_subscription_status_paused"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block in Postgres < 12.
    # On recent versions it's fine; setting autocommit_block defensively.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE subscription_status ADD VALUE IF NOT EXISTS 'paused'")


def downgrade() -> None:
    # Postgres does not support removing enum values. Recreate the type if a true
    # downgrade is needed (omitted here -- this migration is effectively forward-only).
    pass
