"""move trial staff assignment to zone

Revision ID: 20260602_0017
Revises: 20260524_0016
Create Date: 2026-06-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260602_0017"
down_revision: Union[str, None] = "20260524_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("assigned_zone_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_users_assigned_zone_id"), "users", ["assigned_zone_id"], unique=False)
    op.create_foreign_key(
        "fk_users_assigned_zone_id_trial_zones",
        "users",
        "trial_zones",
        ["assigned_zone_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute(
        """
        UPDATE users
        SET assigned_zone_id = trial_studios.trial_zone_id
        FROM trial_studios
        WHERE users.assigned_studio_id = trial_studios.id
          AND users.default_role = 'TRIAL_ZONE_ASSISTANT'
        """
    )
    op.drop_constraint("fk_users_assigned_studio_id_trial_studios", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_assigned_studio_id"), table_name="users")
    op.drop_column("users", "assigned_studio_id")


def downgrade() -> None:
    op.add_column("users", sa.Column("assigned_studio_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_users_assigned_studio_id"), "users", ["assigned_studio_id"], unique=False)
    op.create_foreign_key(
        "fk_users_assigned_studio_id_trial_studios",
        "users",
        "trial_studios",
        ["assigned_studio_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute(
        """
        UPDATE users
        SET assigned_studio_id = (
            SELECT MIN(trial_studios.id)
            FROM trial_studios
            WHERE trial_studios.trial_zone_id = users.assigned_zone_id
        )
        WHERE users.assigned_zone_id IS NOT NULL
        """
    )
    op.drop_constraint("fk_users_assigned_zone_id_trial_zones", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_assigned_zone_id"), table_name="users")
    op.drop_column("users", "assigned_zone_id")
