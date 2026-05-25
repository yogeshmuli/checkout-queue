import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class NotificationModuleType(str, enum.Enum):
    CHECKOUT = "CHECKOUT"
    TRIAL = "TRIAL"


class NotificationType(str, enum.Enum):
    TOKEN_CALLED = "TOKEN_CALLED"
    NEXT_SOON = "NEXT_SOON"


class NotificationChannel(str, enum.Enum):
    SMS = "SMS"


class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


DEFAULT_CALLED_TEMPLATE = "Your token {token_number} has been called. Please proceed to {service_point_name}."
DEFAULT_NEXT_SOON_TEMPLATE = "Your token {token_number} will be called soon. Please stay nearby."


class StoreNotificationConfig(TimestampMixin, Base):
    __tablename__ = "store_notification_configs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    notify_on_called: Mapped[bool] = mapped_column(default=True, nullable=False)
    notify_on_next_soon: Mapped[bool] = mapped_column(default=True, nullable=False)
    called_message_template: Mapped[str] = mapped_column(Text, default=DEFAULT_CALLED_TEMPLATE, nullable=False)
    next_soon_message_template: Mapped[str] = mapped_column(Text, default=DEFAULT_NEXT_SOON_TEMPLATE, nullable=False)

    store = relationship("Store", back_populates="notification_config")


class NotificationLog(TimestampMixin, Base):
    __tablename__ = "notification_logs"
    __table_args__ = (
        UniqueConstraint("module_type", "token_id", "notification_type", name="uq_notification_logs_token_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    module_type: Mapped[NotificationModuleType] = mapped_column(Enum(NotificationModuleType, name="notification_module_type"), index=True, nullable=False)
    token_id: Mapped[int] = mapped_column(index=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(Enum(NotificationType, name="notification_type"), index=True, nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel, name="notification_channel"), default=NotificationChannel.SMS, nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus, name="notification_status"), default=NotificationStatus.PENDING, index=True, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    store = relationship("Store", back_populates="notification_logs")
