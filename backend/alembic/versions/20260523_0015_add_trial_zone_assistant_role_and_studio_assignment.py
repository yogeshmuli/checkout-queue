"""add trial zone assistant role and user studio assignment

Revision ID: 20260523_0015
Revises: 20260523_0014
Create Date: 2026-05-23 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260523_0015"
down_revision: Union[str, None] = "20260523_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'TRIAL_ZONE_ASSISTANT'")

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


def downgrade() -> None:
    op.drop_constraint("fk_users_assigned_studio_id_trial_studios", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_assigned_studio_id"), table_name="users")
    op.drop_column("users", "assigned_studio_id")

    op.execute("UPDATE users SET default_role = 'SUPPORT' WHERE default_role = 'TRIAL_ZONE_ASSISTANT'")
    op.execute("UPDATE user_store_access SET role = 'SUPPORT' WHERE role = 'TRIAL_ZONE_ASSISTANT'")

    op.execute("ALTER TYPE user_role RENAME TO user_role_old")
    op.execute("CREATE TYPE user_role AS ENUM ('SUPER_ADMIN', 'STORE_ADMIN', 'MANAGER', 'CASHIER', 'SUPPORT')")
    op.execute("ALTER TABLE users ALTER COLUMN default_role TYPE user_role USING default_role::text::user_role")
    op.execute("ALTER TABLE user_store_access ALTER COLUMN role TYPE user_role USING role::text::user_role")
    op.execute("DROP TYPE user_role_old")
