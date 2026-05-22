"""add store calendar

Revision ID: 20260522_0009
Revises: 20260522_0008
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260522_0009"
down_revision: Union[str, None] = "20260522_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("store_calendar_days"):
        op.create_table(
            "store_calendar_days",
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
            sa.UniqueConstraint("store_id", "weekday", name="uq_store_calendar_days_store_weekday"),
        )
        op.create_index(op.f("ix_store_calendar_days_id"), "store_calendar_days", ["id"], unique=False)
        op.create_index(op.f("ix_store_calendar_days_store_id"), "store_calendar_days", ["store_id"], unique=False)

    if not inspector.has_table("store_holidays"):
        op.create_table(
            "store_holidays",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("store_id", sa.Integer(), nullable=False),
            sa.Column("holiday_date", sa.Date(), nullable=False),
            sa.Column("name", sa.String(length=150), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("store_id", "holiday_date", name="uq_store_holidays_store_date"),
        )
        op.create_index(op.f("ix_store_holidays_id"), "store_holidays", ["id"], unique=False)
        op.create_index(op.f("ix_store_holidays_store_id"), "store_holidays", ["store_id"], unique=False)

    op.execute(
        """
        INSERT INTO store_calendar_days (
            store_id,
            weekday,
            is_open,
            open_time,
            close_time,
            timezone,
            created_at,
            updated_at
        )
        SELECT stores.id, weekdays.weekday, true, '00:00'::time, '23:59'::time, 'Asia/Kolkata', now(), now()
        FROM stores
        CROSS JOIN generate_series(0, 6) AS weekdays(weekday)
        WHERE NOT EXISTS (
            SELECT 1
            FROM store_calendar_days AS scd
            WHERE scd.store_id = stores.id
            AND scd.weekday = weekdays.weekday
        )
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_store_holidays_store_id"), table_name="store_holidays")
    op.drop_index(op.f("ix_store_holidays_id"), table_name="store_holidays")
    op.drop_table("store_holidays")
    op.drop_index(op.f("ix_store_calendar_days_store_id"), table_name="store_calendar_days")
    op.drop_index(op.f("ix_store_calendar_days_id"), table_name="store_calendar_days")
    op.drop_table("store_calendar_days")
