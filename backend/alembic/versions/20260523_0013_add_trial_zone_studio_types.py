"""add trial zone and studio types

Revision ID: 20260523_0013
Revises: 20260523_0012
Create Date: 2026-05-23 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260523_0013"
down_revision: Union[str, None] = "20260523_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


trial_zone_type = sa.Enum("REGULAR", "EXPRESS", "PRIORITY", name="trial_zone_type")
trial_studio_type = sa.Enum("REGULAR", "EXPRESS", "PRIORITY", name="trial_studio_type")


def upgrade() -> None:
    bind = op.get_bind()
    trial_zone_type.create(bind, checkfirst=True)
    trial_studio_type.create(bind, checkfirst=True)

    op.add_column(
        "trial_zones",
        sa.Column(
            "zone_type",
            trial_zone_type,
            nullable=False,
            server_default="REGULAR",
        ),
    )
    op.add_column(
        "trial_studios",
        sa.Column(
            "studio_type",
            trial_studio_type,
            nullable=False,
            server_default="REGULAR",
        ),
    )

    op.alter_column("trial_zones", "zone_type", server_default=None)
    op.alter_column("trial_studios", "studio_type", server_default=None)


def downgrade() -> None:
    op.drop_column("trial_studios", "studio_type")
    op.drop_column("trial_zones", "zone_type")

    trial_studio_type.drop(op.get_bind(), checkfirst=True)
    trial_zone_type.drop(op.get_bind(), checkfirst=True)
