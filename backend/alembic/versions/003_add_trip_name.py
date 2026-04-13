"""Optionalen Namen für Fahrten hinzufügen

Revision ID: 003
Revises: 002
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "trips",
        sa.Column("name", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("trips", "name")
