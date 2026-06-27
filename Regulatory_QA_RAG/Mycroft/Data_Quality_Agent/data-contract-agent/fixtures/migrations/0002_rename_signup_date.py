"""rename users.signup_date to created_at

Revision ID: 0002_rename_signup_date
Revises: 0001_initial
"""
from alembic import op

revision = "0002_rename_signup_date"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "signup_date", new_column_name="created_at")


def downgrade() -> None:
    op.alter_column("users", "created_at", new_column_name="signup_date")
