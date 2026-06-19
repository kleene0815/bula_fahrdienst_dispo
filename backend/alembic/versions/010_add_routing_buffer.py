"""add routing_buffer_minutes to app_config

Revision ID: 010
Revises: 009
Create Date: 2026-06-16
"""
from alembic import op
import sqlalchemy as sa

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('app_config', sa.Column('routing_buffer_minutes', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    op.drop_column('app_config', 'routing_buffer_minutes')
