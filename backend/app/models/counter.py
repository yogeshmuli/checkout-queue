import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SqlAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class CounterType(str, enum.Enum):
    REGULAR = "REGULAR"
    EXPRESS = "EXPRESS"
    SELF_CHECKOUT = "SELF_CHECKOUT"
    RETURNS_EXCHANGE = "RETURNS_EXCHANGE"
    PRIORITY = "PRIORITY"


class Counter(TimestampMixin, Base):
    __tablename__ = "counters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    section_id: Mapped[int] = mapped_column(
        ForeignKey("checkout_sections.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    counter_type: Mapped[CounterType] = mapped_column(
        SqlAlchemyEnum(CounterType, name="checkout_counter_type"),
        nullable=False,
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    token_prefix: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Timestamp when this counter will be free to serve the next customer
    next_available_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    section = relationship("CheckoutSection", back_populates="counters")
    assigned_users = relationship("User", back_populates="assigned_counter")
    active_tokens = relationship("QueueToken", back_populates="assigned_counter")
