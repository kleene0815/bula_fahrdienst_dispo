"""Add destination_suggestions to app_config

Revision ID: 008
Revises: 007
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('app_config', sa.Column('destination_suggestions', sa.Text(), nullable=False, server_default='[]'))


def downgrade():
    op.drop_column('app_config', 'destination_suggestions')
