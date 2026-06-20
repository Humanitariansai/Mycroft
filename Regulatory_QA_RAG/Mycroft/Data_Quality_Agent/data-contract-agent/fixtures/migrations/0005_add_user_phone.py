"""add users.phone (control: no analytics model reads it)

Revision ID: 0005_add_user_phone
Revises: 0001_initial

A benign migration used as a true-negative control: it adds a column nothing
downstream consumes, so the deterministic layer should report no impact.
"""
import sqlalchemy as sa
from alembic import op

revision = "0005_add_user_phone"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "phone")
