"""Add routing fields to app_config and trips

Revision ID: 009
Revises: 008
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('app_config', sa.Column('camp_address', sa.Text(), nullable=False, server_default=''))
    op.add_column('app_config', sa.Column('routing_api_key', sa.Text(), nullable=True))
    op.add_column('app_config', sa.Column('routing_mode', sa.Text(), nullable=False, server_default='auto'))
    op.add_column('app_config', sa.Column('routing_remaining_requests', sa.Integer(), nullable=True))
    op.add_column('app_config', sa.Column('stop_duration_hinfahrt', sa.Integer(), nullable=False, server_default='10'))
    op.add_column('app_config', sa.Column('stop_duration_abholung', sa.Integer(), nullable=False, server_default='10'))
    op.add_column('app_config', sa.Column('stop_duration_besorgung', sa.Integer(), nullable=False, server_default='15'))

    op.add_column('trips', sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True))
    op.add_column('trips', sa.Column('planned_start_time', sa.DateTime(), nullable=True))
    op.add_column('trips', sa.Column('start_time_manual_override', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    op.drop_column('app_config', 'camp_address')
    op.drop_column('app_config', 'routing_api_key')
    op.drop_column('app_config', 'routing_mode')
    op.drop_column('app_config', 'routing_remaining_requests')
    op.drop_column('app_config', 'stop_duration_hinfahrt')
    op.drop_column('app_config', 'stop_duration_abholung')
    op.drop_column('app_config', 'stop_duration_besorgung')

    op.drop_column('trips', 'estimated_duration_minutes')
    op.drop_column('trips', 'planned_start_time')
    op.drop_column('trips', 'start_time_manual_override')
