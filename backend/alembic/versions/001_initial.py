"""initiales Schema

Revision ID: 001
Revises:
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("keycloak_sub", sa.Text, nullable=False, unique=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("email", sa.Text, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role", sa.Text, nullable=False, primary_key=True),
        sa.CheckConstraint("role IN ('disponent', 'fahrer')", name="user_roles_role_check"),
    )

    op.create_table(
        "vehicles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("license_plate", sa.Text, nullable=False, unique=True),
        sa.Column("seats", sa.Integer, nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("seats >= 1", name="vehicles_seats_check"),
        sa.CheckConstraint("type IN ('fest', 'privat')", name="vehicles_type_check"),
    )

    op.create_table(
        "orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.Text, nullable=False, server_default="offen"),
        sa.Column("priority", sa.Text, nullable=False, server_default="normal"),
        sa.Column("trip_type", sa.Text, nullable=False),
        sa.Column("destination", sa.Text, nullable=False),
        sa.Column("destination_address", sa.Text),
        sa.Column("destination_type", sa.Text, nullable=False),
        sa.Column("deadline", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("patient_name", sa.Text),
        sa.Column("phone", sa.Text),
        sa.Column("companion", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("notes", sa.Text),
        sa.Column("requester_station", sa.Text),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('offen','zugeteilt','unterwegs','erledigt','storniert')", name="orders_status_check"),
        sa.CheckConstraint("priority IN ('normal','mittel','hoch')", name="orders_priority_check"),
        sa.CheckConstraint("trip_type IN ('besorgung','hinfahrt','abholung')", name="orders_trip_type_check"),
        sa.CheckConstraint("destination_type IN ('apotheke','arzt','krankenhaus','sonstiges')", name="orders_destination_type_check"),
        sa.CheckConstraint("companion = false OR patient_name IS NOT NULL", name="orders_companion_requires_patient"),
    )

    op.create_table(
        "trips",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("trip_number", sa.Integer, nullable=False, autoincrement=True),
        sa.Column("status", sa.Text, nullable=False, server_default="geplant"),
        sa.Column("driver_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("vehicle_id", UUID(as_uuid=True), sa.ForeignKey("vehicles.id")),
        sa.Column("qr_token", sa.Text, nullable=False, unique=True),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('geplant','aktiv','abgeschlossen','abgebrochen')", name="trips_status_check"),
    )

    op.create_table(
        "trip_orders",
        sa.Column("trip_id", UUID(as_uuid=True), sa.ForeignKey("trips.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("sort_order", sa.Integer, nullable=False),
    )

    op.create_table(
        "status_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.Text, nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("old_status", sa.Text),
        sa.Column("new_status", sa.Text, nullable=False),
        sa.Column("changed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("changed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("note", sa.Text),
        sa.CheckConstraint("entity_type IN ('order', 'trip')", name="status_log_entity_type_check"),
    )

    op.create_table(
        "app_config",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("security_center_name", sa.Text, nullable=False, server_default=""),
        sa.Column("security_center_phone", sa.Text, nullable=False, server_default=""),
        sa.Column("organizer_name", sa.Text, nullable=False, server_default=""),
        sa.Column("camp_address", sa.Text, nullable=False, server_default=""),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("id = 1", name="app_config_single_row"),
    )

    # Initiale Konfigurationszeile
    op.execute("INSERT INTO app_config (id) VALUES (1)")

    # Indizes
    op.create_index("idx_orders_status", "orders", ["status"])
    op.create_index("idx_orders_deadline", "orders", ["deadline"])
    op.create_index("idx_orders_created_by", "orders", ["created_by"])
    op.create_index("idx_trips_status", "trips", ["status"])
    op.create_index("idx_trips_driver_id", "trips", ["driver_id"])
    op.create_index("idx_status_log_entity", "status_log", ["entity_type", "entity_id"])
    op.create_index("idx_status_log_time", "status_log", ["changed_at"])


def downgrade() -> None:
    op.drop_table("app_config")
    op.drop_table("status_log")
    op.drop_table("trip_orders")
    op.drop_table("trips")
    op.drop_table("orders")
    op.drop_table("vehicles")
    op.drop_table("user_roles")
    op.drop_table("users")
