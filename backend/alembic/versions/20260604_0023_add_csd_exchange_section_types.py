"""add csd exchange section types

Revision ID: 20260604_0023
Revises: 20260604_0022
Create Date: 2026-06-04 00:23:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "20260604_0023"
down_revision: Union[str, None] = "20260604_0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE checkout_section_type ADD VALUE IF NOT EXISTS 'CSD'")
    op.execute("ALTER TYPE checkout_section_type ADD VALUE IF NOT EXISTS 'EXCHANGE'")


def downgrade() -> None:
    # PostgreSQL does not support dropping enum values directly.
    pass
