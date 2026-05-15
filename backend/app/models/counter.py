from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.core.database import Base
from app.models.base import TimestampMixin


class Counter(TimestampMixin, Base):
    __tablename__ = "counters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    section_id: Mapped[int] = mapped_column(
        ForeignKey("checkout_sections.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    counter_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Timestamp when this counter will be free to serve the next customer
    next_available_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    section = relationship("CheckoutSection", back_populates="counters")
    assigned_users = relationship("User", back_populates="assigned_counter")
    active_tokens = relationship("QueueToken", back_populates="assigned_counter")

