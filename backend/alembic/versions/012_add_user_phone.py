"""Fahrer-Kontaktdaten: Telefonnummer am Nutzer

Revision ID: 012
Revises: 011
Create Date: 2026-08-04
"""
import sqlalchemy as sa
from alembic import op

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("users", "phone")
