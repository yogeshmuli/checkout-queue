"""add ML training provenance

Revision ID: 20260804_0026
Revises: 20260604_0025
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260804_0026"
down_revision: Union[str, None] = "20260604_0025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ml_model_metadata", sa.Column("training_source", sa.String(length=30), server_default="DATABASE", nullable=False))
    op.add_column("ml_model_metadata", sa.Column("original_filename", sa.String(length=255), nullable=True))
    op.add_column("ml_model_metadata", sa.Column("source_file_path", sa.Text(), nullable=True))
    op.add_column("ml_model_metadata", sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True))
    op.add_column("ml_model_metadata", sa.Column("validation_summary", sa.Text(), nullable=True))
    op.create_index("ix_ml_model_metadata_uploaded_by_user_id", "ml_model_metadata", ["uploaded_by_user_id"])
    op.create_foreign_key(
        "fk_ml_model_metadata_uploaded_by_user_id_users",
        "ml_model_metadata", "users", ["uploaded_by_user_id"], ["id"], ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_ml_model_metadata_uploaded_by_user_id_users", "ml_model_metadata", type_="foreignkey")
    op.drop_index("ix_ml_model_metadata_uploaded_by_user_id", table_name="ml_model_metadata")
    op.drop_column("ml_model_metadata", "validation_summary")
    op.drop_column("ml_model_metadata", "uploaded_by_user_id")
    op.drop_column("ml_model_metadata", "source_file_path")
    op.drop_column("ml_model_metadata", "original_filename")
    op.drop_column("ml_model_metadata", "training_source")
