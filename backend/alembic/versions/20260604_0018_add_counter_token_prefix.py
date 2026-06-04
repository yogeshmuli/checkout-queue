"""add counter token prefix

Revision ID: 20260604_0018
Revises: 20260602_0017
Create Date: 2026-06-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260604_0018"
down_revision: Union[str, None] = "20260602_0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("counters", sa.Column("token_prefix", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("counters", "token_prefix")
