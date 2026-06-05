import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class TrialStudioType(str, enum.Enum):
    REGULAR = "REGULAR"
    EXPRESS = "EXPRESS"
    PRIORITY = "PRIORITY"


class TrialStudio(TimestampMixin, Base):
    __tablename__ = "trial_studios"
    __table_args__ = (UniqueConstraint("trial_zone_id", "name", name="uq_trial_studios_zone_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    trial_zone_id: Mapped[int] = mapped_column(ForeignKey("trial_zones.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    studio_type: Mapped[TrialStudioType] = mapped_column(
        Enum(TrialStudioType, name="trial_studio_type"),
        nullable=False,
        default=TrialStudioType.REGULAR,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    next_available_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    zone = relationship("TrialZone", back_populates="studios")
    queue_tokens = relationship("TrialQueueToken", back_populates="assigned_studio")
