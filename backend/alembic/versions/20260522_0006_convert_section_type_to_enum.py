"""convert section type to enum

Revision ID: 20260522_0006
Revises: 20260514_0005
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260522_0006"
down_revision: Union[str, None] = "20260514_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


section_type_enum = sa.Enum(
    "REGULAR",
    "EXPRESS",
    "SELF_CHECKOUT",
    "RETURNS",
    "PRIORITY",
    name="checkout_section_type",
)


def upgrade() -> None:
    bind = op.get_bind()
    section_type_enum.create(bind, checkfirst=True)

    op.execute(
        """
        ALTER TABLE checkout_sections
        ALTER COLUMN section_type TYPE checkout_section_type
        USING (
            CASE
                WHEN upper(replace(replace(section_type, '-', '_'), ' ', '_')) IN ('EXPRESS', 'EXPRESS_CHECKOUT')
                    THEN 'EXPRESS'
                WHEN upper(replace(replace(section_type, '-', '_'), ' ', '_')) IN ('SELF_CHECKOUT', 'SELF_SERVICE', 'SELF')
                    THEN 'SELF_CHECKOUT'
                WHEN upper(replace(replace(section_type, '-', '_'), ' ', '_')) IN ('RETURNS', 'RETURNS_EXCHANGE', 'RETURN', 'EXCHANGE')
                    THEN 'RETURNS'
                WHEN upper(replace(replace(section_type, '-', '_'), ' ', '_')) IN ('PRIORITY', 'PRIORITY_CHECKOUT')
                    THEN 'PRIORITY'
                ELSE 'REGULAR'
            END
        )::checkout_section_type
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE checkout_sections
        ALTER COLUMN section_type TYPE VARCHAR(50)
        USING section_type::text
        """
    )

    bind = op.get_bind()
    section_type_enum.drop(bind, checkfirst=True)
