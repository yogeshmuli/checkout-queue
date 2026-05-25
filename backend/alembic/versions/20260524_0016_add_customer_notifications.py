"""add customer notifications

Revision ID: 20260524_0016
Revises: 20260523_0015
Create Date: 2026-05-24 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260524_0016"
down_revision: Union[str, None] = "20260523_0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


notification_module_type = sa.Enum("CHECKOUT", "TRIAL", name="notification_module_type")
notification_type = sa.Enum("TOKEN_CALLED", "NEXT_SOON", name="notification_type")
notification_channel = sa.Enum("SMS", name="notification_channel")
notification_status = sa.Enum("PENDING", "SENT", "FAILED", "SKIPPED", name="notification_status")


def upgrade() -> None:
    notification_module_type.create(op.get_bind(), checkfirst=True)
    notification_type.create(op.get_bind(), checkfirst=True)
    notification_channel.create(op.get_bind(), checkfirst=True)
    notification_status.create(op.get_bind(), checkfirst=True)

    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())

    if "store_notification_configs" not in existing_tables:
        op.create_table(
            "store_notification_configs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("store_id", sa.Integer(), nullable=False),
            sa.Column("is_enabled", sa.Boolean(), nullable=False),
            sa.Column("notify_on_called", sa.Boolean(), nullable=False),
            sa.Column("notify_on_next_soon", sa.Boolean(), nullable=False),
            sa.Column("called_message_template", sa.Text(), nullable=False),
            sa.Column("next_soon_message_template", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("store_id"),
        )
        op.create_index(op.f("ix_store_notification_configs_id"), "store_notification_configs", ["id"], unique=False)
        op.create_index(op.f("ix_store_notification_configs_store_id"), "store_notification_configs", ["store_id"], unique=False)

    if "notification_logs" not in existing_tables:
        op.create_table(
            "notification_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("store_id", sa.Integer(), nullable=False),
            sa.Column("module_type", notification_module_type, nullable=False),
            sa.Column("token_id", sa.Integer(), nullable=False),
            sa.Column("phone_number", sa.String(length=10), nullable=False),
            sa.Column("notification_type", notification_type, nullable=False),
            sa.Column("channel", notification_channel, nullable=False),
            sa.Column("status", notification_status, nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("module_type", "token_id", "notification_type", name="uq_notification_logs_token_type"),
        )
        op.create_index(op.f("ix_notification_logs_id"), "notification_logs", ["id"], unique=False)
        op.create_index(op.f("ix_notification_logs_module_type"), "notification_logs", ["module_type"], unique=False)
        op.create_index(op.f("ix_notification_logs_notification_type"), "notification_logs", ["notification_type"], unique=False)
        op.create_index(op.f("ix_notification_logs_phone_number"), "notification_logs", ["phone_number"], unique=False)
        op.create_index(op.f("ix_notification_logs_status"), "notification_logs", ["status"], unique=False)
        op.create_index(op.f("ix_notification_logs_store_id"), "notification_logs", ["store_id"], unique=False)
        op.create_index(op.f("ix_notification_logs_token_id"), "notification_logs", ["token_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notification_logs_token_id"), table_name="notification_logs")
    op.drop_index(op.f("ix_notification_logs_store_id"), table_name="notification_logs")
    op.drop_index(op.f("ix_notification_logs_status"), table_name="notification_logs")
    op.drop_index(op.f("ix_notification_logs_phone_number"), table_name="notification_logs")
    op.drop_index(op.f("ix_notification_logs_notification_type"), table_name="notification_logs")
    op.drop_index(op.f("ix_notification_logs_module_type"), table_name="notification_logs")
    op.drop_index(op.f("ix_notification_logs_id"), table_name="notification_logs")
    op.drop_table("notification_logs")

    op.drop_index(op.f("ix_store_notification_configs_store_id"), table_name="store_notification_configs")
    op.drop_index(op.f("ix_store_notification_configs_id"), table_name="store_notification_configs")
    op.drop_table("store_notification_configs")

    notification_status.drop(op.get_bind(), checkfirst=True)
    notification_channel.drop(op.get_bind(), checkfirst=True)
    notification_type.drop(op.get_bind(), checkfirst=True)
    notification_module_type.drop(op.get_bind(), checkfirst=True)
