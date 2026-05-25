from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Store(TimestampMixin, Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    manager_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    manager_phone: Mapped[str | None] = mapped_column(String(10), nullable=True)
    spoc_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    spoc_phone: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    checkout_sections = relationship("CheckoutSection", back_populates="store", cascade="all, delete-orphan")
    queue_tokens = relationship("QueueToken", back_populates="store", cascade="all, delete-orphan")
    config = relationship("StoreConfig", back_populates="store", cascade="all, delete-orphan", uselist=False)
    calendar_days = relationship("StoreCalendarDay", back_populates="store", cascade="all, delete-orphan")
    holidays = relationship("StoreHoliday", back_populates="store", cascade="all, delete-orphan")
    calendar_events = relationship("StoreCalendarEvent", back_populates="store", cascade="all, delete-orphan")
    trial_zones = relationship("TrialZone", back_populates="store", cascade="all, delete-orphan")
    trial_config = relationship("TrialStoreConfig", back_populates="store", cascade="all, delete-orphan", uselist=False)
    trial_calendar_days = relationship("TrialCalendarDay", back_populates="store", cascade="all, delete-orphan")
    trial_holidays = relationship("TrialHoliday", back_populates="store", cascade="all, delete-orphan")
    trial_calendar_events = relationship("TrialCalendarEvent", back_populates="store", cascade="all, delete-orphan")
    trial_queue_tokens = relationship("TrialQueueToken", back_populates="store", cascade="all, delete-orphan")
    notification_config = relationship("StoreNotificationConfig", back_populates="store", cascade="all, delete-orphan", uselist=False)
    notification_logs = relationship("NotificationLog", back_populates="store", cascade="all, delete-orphan")
