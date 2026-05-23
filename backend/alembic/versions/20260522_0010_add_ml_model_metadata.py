"""add ml model metadata

Revision ID: 20260522_0010
Revises: 20260522_0009
Create Date: 2026-05-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260522_0010"
down_revision: Union[str, None] = "20260522_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("ml_model_metadata"):
        return

    op.create_table(
        "ml_model_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("model_type", sa.String(length=80), nullable=False),
        sa.Column("model_version", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("artifact_path", sa.Text(), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mae", sa.Float(), nullable=True),
        sa.Column("r2_score", sa.Float(), nullable=True),
        sa.Column("accuracy_score", sa.Float(), nullable=True),
        sa.Column("data_quality_score", sa.Float(), nullable=True),
        sa.Column("feature_importance", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ml_model_metadata_id"), "ml_model_metadata", ["id"], unique=False)
    op.create_index(op.f("ix_ml_model_metadata_status"), "ml_model_metadata", ["status"], unique=False)
    op.create_index(op.f("ix_ml_model_metadata_store_id"), "ml_model_metadata", ["store_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ml_model_metadata_store_id"), table_name="ml_model_metadata")
    op.drop_index(op.f("ix_ml_model_metadata_status"), table_name="ml_model_metadata")
    op.drop_index(op.f("ix_ml_model_metadata_id"), table_name="ml_model_metadata")
    op.drop_table("ml_model_metadata")
