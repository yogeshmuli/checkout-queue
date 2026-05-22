"""convert counter type to enum

Revision ID: 20260522_0008
Revises: 20260522_0007
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260522_0008"
down_revision: Union[str, None] = "20260522_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


counter_type_enum = sa.Enum(
    "REGULAR",
    "EXPRESS",
    "SELF_CHECKOUT",
    "RETURNS_EXCHANGE",
    "PRIORITY",
    name="checkout_counter_type",
)


def upgrade() -> None:
    bind = op.get_bind()
    counter_type_enum.create(bind, checkfirst=True)

    op.execute(
        """
        ALTER TABLE counters
        ALTER COLUMN counter_type TYPE checkout_counter_type
        USING (
            CASE
                WHEN upper(replace(replace(counter_type, '-', '_'), ' ', '_')) IN ('EXPRESS', 'EXPRESS_CHECKOUT')
                    THEN 'EXPRESS'
                WHEN upper(replace(replace(counter_type, '-', '_'), ' ', '_')) IN ('SELF_CHECKOUT', 'SELF_SERVICE', 'SELF')
                    THEN 'SELF_CHECKOUT'
                WHEN upper(replace(replace(counter_type, '-', '_'), ' ', '_')) IN ('RETURNS_EXCHANGE', 'RETURNS', 'RETURN', 'EXCHANGE')
                    THEN 'RETURNS_EXCHANGE'
                WHEN upper(replace(replace(counter_type, '-', '_'), ' ', '_')) IN ('PRIORITY', 'PRIORITY_CHECKOUT')
                    THEN 'PRIORITY'
                ELSE 'REGULAR'
            END
        )::checkout_counter_type
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE counters
        ALTER COLUMN counter_type TYPE VARCHAR(50)
        USING counter_type::text
        """
    )

    bind = op.get_bind()
    counter_type_enum.drop(bind, checkfirst=True)
