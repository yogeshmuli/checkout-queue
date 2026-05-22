from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class StoreConfig(TimestampMixin, Base):
    __tablename__ = "store_configs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    token_id_prefix: Mapped[str | None] = mapped_column(String(20), nullable=True)
    base_service_minutes: Mapped[int] = mapped_column(default=4, nullable=False)
    per_item_service_minutes: Mapped[float] = mapped_column(Float, default=0.25, nullable=False)
    min_service_minutes: Mapped[int] = mapped_column(default=5, nullable=False)

    store = relationship("Store", back_populates="config")
