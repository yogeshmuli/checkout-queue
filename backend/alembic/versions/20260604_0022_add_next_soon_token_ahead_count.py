"""add next soon token ahead count

Revision ID: 20260604_0022
Revises: 20260604_0021
Create Date: 2026-06-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260604_0022"
down_revision: Union[str, None] = "20260604_0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "store_notification_configs",
        sa.Column("next_soon_token_ahead_count", sa.Integer(), nullable=False, server_default="2"),
    )
    op.alter_column("store_notification_configs", "next_soon_token_ahead_count", server_default=None)


def downgrade() -> None:
    op.drop_column("store_notification_configs", "next_soon_token_ahead_count")
