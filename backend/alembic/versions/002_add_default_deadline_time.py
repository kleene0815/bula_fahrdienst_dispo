"""Standard-Deadline-Uhrzeit zur App-Konfiguration hinzufügen

Revision ID: 002
Revises: 001
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "app_config",
        sa.Column("default_deadline_time", sa.Text, nullable=False, server_default="17:00"),
    )


def downgrade() -> None:
    op.drop_column("app_config", "default_deadline_time")
