"""add store configs

Revision ID: 20260522_0007
Revises: 20260522_0006
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260522_0007"
down_revision: Union[str, None] = "20260522_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("store_configs"):
        op.create_table(
            "store_configs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("store_id", sa.Integer(), nullable=False),
            sa.Column("token_id_prefix", sa.String(length=20), nullable=True),
            sa.Column("base_service_minutes", sa.Integer(), nullable=False),
            sa.Column("per_item_service_minutes", sa.Float(), nullable=False),
            sa.Column("min_service_minutes", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("store_id"),
        )
        op.create_index(op.f("ix_store_configs_id"), "store_configs", ["id"], unique=False)
        op.create_index(op.f("ix_store_configs_store_id"), "store_configs", ["store_id"], unique=True)

    op.execute(
        """
        INSERT INTO store_configs (
            store_id,
            token_id_prefix,
            base_service_minutes,
            per_item_service_minutes,
            min_service_minutes,
            created_at,
            updated_at
        )
        SELECT id, NULL, 4, 0.25, 5, now(), now()
        FROM stores AS s
        WHERE NOT EXISTS (
            SELECT 1
            FROM store_configs AS sc
            WHERE sc.store_id = s.id
        )
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_store_configs_store_id"), table_name="store_configs")
    op.drop_index(op.f("ix_store_configs_id"), table_name="store_configs")
    op.drop_table("store_configs")
