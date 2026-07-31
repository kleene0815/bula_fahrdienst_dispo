"""Automatische Rückfahrt: create_return_order-Flag, Status 'erwartete_rueckfahrt', Deadline nullable

Revision ID: 011
Revises: 010
Create Date: 2026-07-31
"""
import sqlalchemy as sa
from alembic import op

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("create_return_order", sa.Boolean, nullable=False, server_default="false"),
    )
    op.alter_column("orders", "deadline", nullable=True)
    op.drop_constraint("orders_status_check", "orders")
    op.create_check_constraint(
        "orders_status_check",
        "orders",
        "status IN ('offen','erwartete_rueckfahrt','zugeteilt','unterwegs','erledigt','storniert')",
    )


def downgrade() -> None:
    op.drop_constraint("orders_status_check", "orders")
    op.create_check_constraint(
        "orders_status_check",
        "orders",
        "status IN ('offen','zugeteilt','unterwegs','erledigt','storniert')",
    )
    op.alter_column("orders", "deadline", nullable=False)
    op.drop_column("orders", "create_return_order")
