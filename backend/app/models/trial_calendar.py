import enum
from datetime import date, time

from sqlalchemy import Boolean, Date, Enum, ForeignKey, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class TrialCalendarEventType(str, enum.Enum):
    PROMOTION = "PROMOTION"
    SALE = "SALE"
    HOLIDAY = "HOLIDAY"
    OTHER = "OTHER"


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
