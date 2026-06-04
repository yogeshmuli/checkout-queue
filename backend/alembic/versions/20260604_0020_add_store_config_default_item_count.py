"""add store config default item count

Revision ID: 20260604_0020
Revises: 20260604_0019
Create Date: 2026-06-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260604_0020"
down_revision: Union[str, None] = "20260604_0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "store_configs",
        sa.Column("default_item_count", sa.Integer(), nullable=False, server_default="10"),
    )
    op.alter_column("store_configs", "default_item_count", server_default=None)


def downgrade() -> None:
    op.drop_column("store_configs", "default_item_count")
