"""gender like trial zone types

Revision ID: 20260604_0024
Revises: 20260604_0023
Create Date: 2026-06-04 00:24:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "20260604_0024"
down_revision: Union[str, None] = "20260604_0023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE trial_zones ALTER COLUMN zone_type TYPE TEXT USING zone_type::text")
    op.execute(
        """
        UPDATE trial_zones
        SET zone_type = CASE
            WHEN zone_type IN ('MALE', 'FEMALE', 'UNISEX') THEN zone_type
            ELSE 'UNISEX'
        END
        """
    )
    op.execute("DROP TYPE trial_zone_type")
    op.execute("CREATE TYPE trial_zone_type AS ENUM ('MALE', 'FEMALE', 'UNISEX')")
    op.execute("ALTER TABLE trial_zones ALTER COLUMN zone_type TYPE trial_zone_type USING zone_type::trial_zone_type")
    op.execute("UPDATE trial_zones SET gender = zone_type::text::trial_zone_gender")


def downgrade() -> None:
    op.execute("ALTER TABLE trial_zones ALTER COLUMN zone_type TYPE TEXT USING zone_type::text")
    op.execute("UPDATE trial_zones SET zone_type = 'REGULAR'")
    op.execute("DROP TYPE trial_zone_type")
    op.execute("CREATE TYPE trial_zone_type AS ENUM ('REGULAR', 'EXPRESS', 'PRIORITY')")
    op.execute("ALTER TABLE trial_zones ALTER COLUMN zone_type TYPE trial_zone_type USING zone_type::trial_zone_type")
