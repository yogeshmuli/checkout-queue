import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class TrialQueueTokenStatus(str, enum.Enum):
    WAITING = "WAITING"
    CALLED = "CALLED"
    SERVING = "SERVING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class TrialQueueToken(TimestampMixin, Base):
    __tablename__ = "trial_queue_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    trial_zone_id: Mapped[int | None] = mapped_column(ForeignKey("trial_zones.id", ondelete="SET NULL"), index=True)
    assigned_studio_id: Mapped[int | None] = mapped_column(ForeignKey("trial_studios.id", ondelete="SET NULL"), index=True)
    token_number: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    status: Mapped[TrialQueueTokenStatus] = mapped_column(
        Enum(TrialQueueTokenStatus, name="trial_queue_token_status"),
        default=TrialQueueTokenStatus.WAITING,
        index=True,
        nullable=False,
    )
    item_count: Mapped[int | None] = mapped_column(nullable=True)
    customer_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    service_time_minutes: Mapped[int | None] = mapped_column(nullable=True)
    calculation_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    calling_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    called_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    service_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    store = relationship("Store", back_populates="trial_queue_tokens")
    zone = relationship("TrialZone", back_populates="queue_tokens")
    assigned_studio = relationship("TrialStudio", back_populates="queue_tokens")
