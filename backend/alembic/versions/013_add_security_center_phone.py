"""Telefonnummer der Sicherheitszentrale in der App-Konfiguration

Revision ID: 013
Revises: 012
Create Date: 2026-08-04
"""
import sqlalchemy as sa
from alembic import op

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "app_config",
        sa.Column("security_center_phone", sa.Text, nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("app_config", "security_center_phone")
