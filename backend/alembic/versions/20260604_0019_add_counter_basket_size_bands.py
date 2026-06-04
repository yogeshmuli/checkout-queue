"""add counter basket size bands

Revision ID: 20260604_0019
Revises: 20260604_0018
Create Date: 2026-06-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260604_0019"
down_revision: Union[str, None] = "20260604_0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "counters",
        sa.Column("basket_size_bands", postgresql.ARRAY(sa.String(length=20)), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("counters", "basket_size_bands")
