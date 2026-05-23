"""add store calendar events

Revision ID: 20260522_0011
Revises: 20260522_0010
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260522_0011"
down_revision: Union[str, None] = "20260522_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


event_type = sa.Enum("PROMOTION", "SALE", "HOLIDAY", "OTHER", name="store_calendar_event_type")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    event_type.create(bind, checkfirst=True)

    if inspector.has_table("store_calendar_events"):
        return

    op.create_table(
        "store_calendar_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=True),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "event_date", "event_type", "name", name="uq_store_calendar_events_store_date_type_name"),
    )
    op.create_index(op.f("ix_store_calendar_events_event_date"), "store_calendar_events", ["event_date"], unique=False)
    op.create_index(op.f("ix_store_calendar_events_id"), "store_calendar_events", ["id"], unique=False)
    op.create_index(op.f("ix_store_calendar_events_store_id"), "store_calendar_events", ["store_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_store_calendar_events_store_id"), table_name="store_calendar_events")
    op.drop_index(op.f("ix_store_calendar_events_id"), table_name="store_calendar_events")
    op.drop_index(op.f("ix_store_calendar_events_event_date"), table_name="store_calendar_events")
    op.drop_table("store_calendar_events")
    event_type.drop(op.get_bind(), checkfirst=True)
