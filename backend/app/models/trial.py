import enum
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, String, Text, Time, UniqueConstraint
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


class TrialCalendarEventType(str, enum.Enum):
    PROMOTION = "PROMOTION"
    SALE = "SALE"
    HOLIDAY = "HOLIDAY"
    OTHER = "OTHER"


class TrialZone(TimestampMixin, Base):
    __tablename__ = "trial_zones"
    __table_args__ = (UniqueConstraint("store_id", "name", name="uq_trial_zones_store_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    store = relationship("Store", back_populates="trial_zones")
    studios = relationship("TrialStudio", back_populates="zone", cascade="all, delete-orphan")
    queue_tokens = relationship("TrialQueueToken", back_populates="zone")


class TrialStudio(TimestampMixin, Base):
    __tablename__ = "trial_studios"
    __table_args__ = (UniqueConstraint("trial_zone_id", "name", name="uq_trial_studios_zone_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    trial_zone_id: Mapped[int] = mapped_column(ForeignKey("trial_zones.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    next_available_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    zone = relationship("TrialZone", back_populates="studios")
    queue_tokens = relationship("TrialQueueToken", back_populates="assigned_studio")


class TrialStoreConfig(TimestampMixin, Base):
    __tablename__ = "trial_store_configs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    token_id_prefix: Mapped[str | None] = mapped_column(String(20), nullable=True)
    base_service_minutes: Mapped[int] = mapped_column(default=8, nullable=False)
    per_unit_service_minutes: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    min_service_minutes: Mapped[int] = mapped_column(default=10, nullable=False)

    store = relationship("Store", back_populates="trial_config")


class TrialCalendarDay(TimestampMixin, Base):
    __tablename__ = "trial_calendar_days"
    __table_args__ = (UniqueConstraint("store_id", "weekday", name="uq_trial_calendar_days_store_weekday"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    weekday: Mapped[int] = mapped_column(nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    open_time: Mapped[time] = mapped_column(Time(), nullable=False)
    close_time: Mapped[time] = mapped_column(Time(), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata", nullable=False)

    store = relationship("Store", back_populates="trial_calendar_days")


class TrialHoliday(TimestampMixin, Base):
    __tablename__ = "trial_holidays"
    __table_args__ = (UniqueConstraint("store_id", "holiday_date", name="uq_trial_holidays_store_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    holiday_date: Mapped[date] = mapped_column(Date(), nullable=False)
    name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    store = relationship("Store", back_populates="trial_holidays")


class TrialCalendarEvent(TimestampMixin, Base):
    __tablename__ = "trial_calendar_events"
    __table_args__ = (
        UniqueConstraint("store_id", "event_date", "event_type", "name", name="uq_trial_calendar_events_store_date_type_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    event_date: Mapped[date] = mapped_column(Date(), index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    event_type: Mapped[TrialCalendarEventType] = mapped_column(Enum(TrialCalendarEventType, name="trial_calendar_event_type"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    store = relationship("Store", back_populates="trial_calendar_events")


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
