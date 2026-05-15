"""make counters next_available_time timezone aware

Revision ID: 20260508_0004
Revises: 4f3122197651
Create Date: 2026-05-08 13:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260508_0004"
down_revision: Union[str, None] = "4f3122197651"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "counters",
        "next_available_time",
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using="next_available_time AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        "counters",
        "next_available_time",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
        postgresql_using="next_available_time AT TIME ZONE 'UTC'",
    )
