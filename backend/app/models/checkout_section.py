import enum

from sqlalchemy import ForeignKey, String
from sqlalchemy import Enum as SqlAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class CheckoutSectionType(str, enum.Enum):
    CSD = "CSD"
    REGULAR = "REGULAR"
    EXPRESS = "EXPRESS"
    SELF_CHECKOUT = "SELF_CHECKOUT"
    RETURNS = "RETURNS"
    EXCHANGE = "EXCHANGE"
    PRIORITY = "PRIORITY"


class CheckoutSection(TimestampMixin, Base):
    __tablename__ = "checkout_sections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    section_type: Mapped[CheckoutSectionType] = mapped_column(
        SqlAlchemyEnum(CheckoutSectionType, name="checkout_section_type"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    store = relationship("Store", back_populates="checkout_sections")
    counters = relationship("Counter", back_populates="section", cascade="all, delete-orphan")
    queue_tokens = relationship("QueueToken", back_populates="section")
