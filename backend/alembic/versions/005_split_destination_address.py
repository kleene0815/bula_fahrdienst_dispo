"""destination_address in destination_street und destination_city aufteilen

Revision ID: 005
Revises: 004
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("destination_street", sa.Text, nullable=True))
    op.add_column("orders", sa.Column("destination_city", sa.Text, nullable=True))

    # Bestehende destination_address in destination_street übernehmen
    op.execute("UPDATE orders SET destination_street = destination_address WHERE destination_address IS NOT NULL")

    op.drop_column("orders", "destination_address")


def downgrade() -> None:
    op.add_column("orders", sa.Column("destination_address", sa.Text, nullable=True))
    op.execute(
        """
        UPDATE orders SET destination_address =
            CASE
                WHEN destination_street IS NOT NULL AND destination_city IS NOT NULL
                    THEN destination_street || ', ' || destination_city
                WHEN destination_street IS NOT NULL
                    THEN destination_street
                WHEN destination_city IS NOT NULL
                    THEN destination_city
                ELSE NULL
            END
        """
    )
    op.drop_column("orders", "destination_city")
    op.drop_column("orders", "destination_street")
