"""Replace config contact fields with printout_header_html

Revision ID: 006
Revises: 005
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('app_config', sa.Column('printout_header_html', sa.Text(), nullable=False, server_default=''))
    op.drop_column('app_config', 'security_center_name')
    op.drop_column('app_config', 'security_center_phone')
    op.drop_column('app_config', 'organizer_name')
    op.drop_column('app_config', 'camp_address')


def downgrade():
    op.add_column('app_config', sa.Column('camp_address', sa.Text(), nullable=False, server_default=''))
    op.add_column('app_config', sa.Column('organizer_name', sa.Text(), nullable=False, server_default=''))
    op.add_column('app_config', sa.Column('security_center_phone', sa.Text(), nullable=False, server_default=''))
    op.add_column('app_config', sa.Column('security_center_name', sa.Text(), nullable=False, server_default=''))
    op.drop_column('app_config', 'printout_header_html')
