"""Add created_at to trip_orders and started_at to trips

Revision ID: 007
Revises: 006
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('trip_orders', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.add_column('trips', sa.Column('started_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('trip_orders', 'created_at')
    op.drop_column('trips', 'started_at')
