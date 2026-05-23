"""add trial zone gender

Revision ID: 20260523_0014
Revises: 20260523_0013
Create Date: 2026-05-23 00:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260523_0014"
down_revision: Union[str, None] = "20260523_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


trial_zone_gender = sa.Enum("MALE", "FEMALE", "UNISEX", name="trial_zone_gender")


def upgrade() -> None:
    bind = op.get_bind()
    trial_zone_gender.create(bind, checkfirst=True)

    op.add_column(
        "trial_zones",
        sa.Column(
            "gender",
            trial_zone_gender,
            nullable=False,
            server_default="UNISEX",
        ),
    )

    op.alter_column("trial_zones", "gender", server_default=None)


def downgrade() -> None:
    op.drop_column("trial_zones", "gender")

    trial_zone_gender.drop(op.get_bind(), checkfirst=True)
