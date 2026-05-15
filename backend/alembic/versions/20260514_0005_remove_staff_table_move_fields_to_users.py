"""remove staff table and move assignment fields to users

Revision ID: 20260514_0005
Revises: 030389d488c1
Create Date: 2026-05-14 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260514_0005"
down_revision: Union[str, None] = "030389d488c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("store_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("section_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("assigned_counter_id", sa.Integer(), nullable=True))

    op.create_index(op.f("ix_users_store_id"), "users", ["store_id"], unique=False)
    op.create_index(op.f("ix_users_section_id"), "users", ["section_id"], unique=False)
    op.create_index(op.f("ix_users_assigned_counter_id"), "users", ["assigned_counter_id"], unique=False)

    op.create_foreign_key(
        "fk_users_store_id_stores",
        "users",
        "stores",
        ["store_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_users_section_id_checkout_sections",
        "users",
        "checkout_sections",
        ["section_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_users_assigned_counter_id_counters",
        "users",
        "counters",
        ["assigned_counter_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.drop_index(op.f("ix_users_staff_id"), table_name="users")
    op.drop_constraint("users_staff_id_fkey", "users", type_="foreignkey")
    op.drop_column("users", "staff_id")

    op.drop_index(op.f("ix_staff_store_id"), table_name="staff")
    op.drop_index(op.f("ix_staff_section_id"), table_name="staff")
    op.drop_index(op.f("ix_staff_phone_number"), table_name="staff")
    op.drop_index(op.f("ix_staff_id"), table_name="staff")
    op.drop_index(op.f("ix_staff_assigned_counter_id"), table_name="staff")
    op.drop_table("staff")


def downgrade() -> None:
    op.create_table(
        "staff",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=True),
        sa.Column("assigned_counter_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("phone_number", sa.String(length=10), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_counter_id"], ["counters.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["section_id"], ["checkout_sections.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_staff_assigned_counter_id"), "staff", ["assigned_counter_id"], unique=False)
    op.create_index(op.f("ix_staff_id"), "staff", ["id"], unique=False)
    op.create_index(op.f("ix_staff_phone_number"), "staff", ["phone_number"], unique=False)
    op.create_index(op.f("ix_staff_section_id"), "staff", ["section_id"], unique=False)
    op.create_index(op.f("ix_staff_store_id"), "staff", ["store_id"], unique=False)

    op.add_column("users", sa.Column("staff_id", sa.Integer(), nullable=True))
    op.create_foreign_key("users_staff_id_fkey", "users", "staff", ["staff_id"], ["id"], ondelete="SET NULL")
    op.create_index(op.f("ix_users_staff_id"), "users", ["staff_id"], unique=False)

    op.drop_constraint("fk_users_assigned_counter_id_counters", "users", type_="foreignkey")
    op.drop_constraint("fk_users_section_id_checkout_sections", "users", type_="foreignkey")
    op.drop_constraint("fk_users_store_id_stores", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_assigned_counter_id"), table_name="users")
    op.drop_index(op.f("ix_users_section_id"), table_name="users")
    op.drop_index(op.f("ix_users_store_id"), table_name="users")
    op.drop_column("users", "assigned_counter_id")
    op.drop_column("users", "section_id")
    op.drop_column("users", "store_id")
