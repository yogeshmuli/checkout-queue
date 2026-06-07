"""add checkout shared queue flag

Revision ID: 20260604_0021
Revises: 20260604_0020
Create Date: 2026-06-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260604_0021"
down_revision: Union[str, None] = "20260604_0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "store_configs",
        sa.Column("shared_queue_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("store_configs", "shared_queue_enabled", server_default=None)


def downgrade() -> None:
    op.drop_column("store_configs", "shared_queue_enabled")
