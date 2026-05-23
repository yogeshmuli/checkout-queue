"""add trial queue module

Revision ID: 20260523_0012
Revises: 20260522_0011
Create Date: 2026-05-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260523_0012"
down_revision: Union[str, None] = "20260522_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


trial_token_status = sa.Enum("WAITING", "CALLED", "SERVING", "COMPLETED", "CANCELLED", "NO_SHOW", name="trial_queue_token_status")
trial_event_type = sa.Enum("PROMOTION", "SALE", "HOLIDAY", "OTHER", name="trial_calendar_event_type")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    trial_token_status.create(bind, checkfirst=True)
    trial_event_type.create(bind, checkfirst=True)

    if not inspector.has_table("trial_zones"):
        op.create_table(
            "trial_zones",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("store_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("store_id", "name", name="uq_trial_zones_store_name"),
        )
        op.create_index(op.f("ix_trial_zones_id"), "trial_zones", ["id"], unique=False)
        op.create_index(op.f("ix_trial_zones_store_id"), "trial_zones", ["store_id"], unique=False)

    if not inspector.has_table("trial_studios"):
        op.create_table(
            "trial_studios",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("trial_zone_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("next_available_time", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["trial_zone_id"], ["trial_zones.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("trial_zone_id", "name", name="uq_trial_studios_zone_name"),
        )
        op.create_index(op.f("ix_trial_studios_id"), "trial_studios", ["id"], unique=False)
        op.create_index(op.f("ix_trial_studios_trial_zone_id"), "trial_studios", ["trial_zone_id"], unique=False)

    if not inspector.has_table("trial_store_configs"):
        op.create_table(
            "trial_store_configs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("store_id", sa.Integer(), nullable=False),
            sa.Column("token_id_prefix", sa.String(length=20), nullable=True),
            sa.Column("base_service_minutes", sa.Integer(), nullable=False),
            sa.Column("per_unit_service_minutes", sa.Float(), nullable=False),
            sa.Column("min_service_minutes", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("store_id"),
        )
        op.create_index(op.f("ix_trial_store_configs_id"), "trial_store_configs", ["id"], unique=False)
        op.create_index(op.f("ix_trial_store_configs_store_id"), "trial_store_configs", ["store_id"], unique=False)

    if not inspector.has_table("trial_calendar_days"):
        op.create_table(
            "trial_calendar_days",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("store_id", sa.Integer(), nullable=False),
            sa.Column("weekday", sa.Integer(), nullable=False),
            sa.Column("is_open", sa.Boolean(), nullable=False),
            sa.Column("open_time", sa.Time(), nullable=False),
            sa.Column("close_time", sa.Time(), nullable=False),
            sa.Column("timezone", sa.String(length=64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("store_id", "weekday", name="uq_trial_calendar_days_store_weekday"),
        )
        op.create_index(op.f("ix_trial_calendar_days_id"), "trial_calendar_days", ["id"], unique=False)
        op.create_index(op.f("ix_trial_calendar_days_store_id"), "trial_calendar_days", ["store_id"], unique=False)

    if not inspector.has_table("trial_holidays"):
        op.create_table(
            "trial_holidays",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("store_id", sa.Integer(), nullable=False),
            sa.Column("holiday_date", sa.Date(), nullable=False),
            sa.Column("name", sa.String(length=150), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("store_id", "holiday_date", name="uq_trial_holidays_store_date"),
        )
        op.create_index(op.f("ix_trial_holidays_id"), "trial_holidays", ["id"], unique=False)
        op.create_index(op.f("ix_trial_holidays_store_id"), "trial_holidays", ["store_id"], unique=False)

    if not inspector.has_table("trial_calendar_events"):
        op.create_table(
            "trial_calendar_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("store_id", sa.Integer(), nullable=False),
            sa.Column("event_date", sa.Date(), nullable=False),
            sa.Column("name", sa.String(length=150), nullable=True),
            sa.Column("event_type", trial_event_type, nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("store_id", "event_date", "event_type", "name", name="uq_trial_calendar_events_store_date_type_name"),
        )
        op.create_index(op.f("ix_trial_calendar_events_event_date"), "trial_calendar_events", ["event_date"], unique=False)
        op.create_index(op.f("ix_trial_calendar_events_id"), "trial_calendar_events", ["id"], unique=False)
        op.create_index(op.f("ix_trial_calendar_events_store_id"), "trial_calendar_events", ["store_id"], unique=False)

    if not inspector.has_table("trial_queue_tokens"):
        op.create_table(
            "trial_queue_tokens",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("store_id", sa.Integer(), nullable=False),
            sa.Column("trial_zone_id", sa.Integer(), nullable=True),
            sa.Column("assigned_studio_id", sa.Integer(), nullable=True),
            sa.Column("token_number", sa.String(length=30), nullable=False),
            sa.Column("phone_number", sa.String(length=10), nullable=False),
            sa.Column("status", trial_token_status, nullable=False),
            sa.Column("item_count", sa.Integer(), nullable=True),
            sa.Column("customer_type", sa.String(length=50), nullable=True),
            sa.Column("service_time_minutes", sa.Integer(), nullable=True),
            sa.Column("calculation_method", sa.String(length=50), nullable=True),
            sa.Column("calling_time", sa.DateTime(timezone=True), nullable=True),
            sa.Column("called_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("service_started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancellation_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["assigned_studio_id"], ["trial_studios.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["trial_zone_id"], ["trial_zones.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        for column in ("id", "store_id", "trial_zone_id", "assigned_studio_id", "token_number", "phone_number", "status"):
            op.create_index(op.f(f"ix_trial_queue_tokens_{column}"), "trial_queue_tokens", [column], unique=False)

    op.execute(
        """
        INSERT INTO trial_calendar_days (store_id, weekday, is_open, open_time, close_time, timezone, created_at, updated_at)
        SELECT stores.id, weekdays.weekday, true, '00:00'::time, '23:59'::time, 'Asia/Kolkata', now(), now()
        FROM stores
        CROSS JOIN generate_series(0, 6) AS weekdays(weekday)
        WHERE NOT EXISTS (
            SELECT 1 FROM trial_calendar_days AS tcd
            WHERE tcd.store_id = stores.id AND tcd.weekday = weekdays.weekday
        )
        """
    )


def downgrade() -> None:
    op.drop_table("trial_queue_tokens")
    op.drop_table("trial_calendar_events")
    op.drop_table("trial_holidays")
    op.drop_table("trial_calendar_days")
    op.drop_table("trial_store_configs")
    op.drop_table("trial_studios")
    op.drop_table("trial_zones")
    trial_event_type.drop(op.get_bind(), checkfirst=True)
    trial_token_status.drop(op.get_bind(), checkfirst=True)
