"""Priority-Constraint auf gering/normal/hoch aktualisieren

Revision ID: 004
Revises: 003
Create Date: 2026-04-13
"""
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("orders_priority_check", "orders")
    op.create_check_constraint(
        "orders_priority_check",
        "orders",
        "priority IN ('gering', 'normal', 'hoch')",
    )


def downgrade() -> None:
    op.drop_constraint("orders_priority_check", "orders")
    op.create_check_constraint(
        "orders_priority_check",
        "orders",
        "priority IN ('normal', 'mittel', 'hoch')",
    )
