from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class MLModelMetadata(TimestampMixin, Base):
    __tablename__ = "ml_model_metadata"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    model_type: Mapped[str] = mapped_column(String(80), nullable=False)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="READY", index=True, nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    r2_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feature_importance: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
