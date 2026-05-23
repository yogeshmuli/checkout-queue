import enum
from datetime import date, time

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy import Enum as SqlAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class StoreCalendarDay(TimestampMixin, Base):
    __tablename__ = "store_calendar_days"
    __table_args__ = (UniqueConstraint("store_id", "weekday", name="uq_store_calendar_days_store_weekday"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    open_time: Mapped[time] = mapped_column(Time(), nullable=False)
    close_time: Mapped[time] = mapped_column(Time(), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata", nullable=False)

    store = relationship("Store", back_populates="calendar_days")


class StoreHoliday(TimestampMixin, Base):
    __tablename__ = "store_holidays"
    __table_args__ = (UniqueConstraint("store_id", "holiday_date", name="uq_store_holidays_store_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    holiday_date: Mapped[date] = mapped_column(Date(), nullable=False)
    name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    store = relationship("Store", back_populates="holidays")


class StoreCalendarEventType(str, enum.Enum):
    PROMOTION = "PROMOTION"
    SALE = "SALE"
    HOLIDAY = "HOLIDAY"
    OTHER = "OTHER"


class StoreCalendarEvent(TimestampMixin, Base):
    __tablename__ = "store_calendar_events"
    __table_args__ = (
        UniqueConstraint("store_id", "event_date", "event_type", "name", name="uq_store_calendar_events_store_date_type_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    event_date: Mapped[date] = mapped_column(Date(), index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    event_type: Mapped[StoreCalendarEventType] = mapped_column(
        SqlAlchemyEnum(StoreCalendarEventType, name="store_calendar_event_type"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    store = relationship("Store", back_populates="calendar_events")
