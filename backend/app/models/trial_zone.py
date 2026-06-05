import enum

from sqlalchemy import Boolean, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class TrialZoneType(str, enum.Enum):
    REGULAR = "REGULAR"
    EXPRESS = "EXPRESS"
    PRIORITY = "PRIORITY"


class TrialZoneGender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    UNISEX = "UNISEX"


class TrialZone(TimestampMixin, Base):
    __tablename__ = "trial_zones"
    __table_args__ = (UniqueConstraint("store_id", "name", name="uq_trial_zones_store_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    zone_type: Mapped[TrialZoneType] = mapped_column(Enum(TrialZoneType, name="trial_zone_type"), nullable=False, default=TrialZoneType.REGULAR)
    gender: Mapped[TrialZoneGender] = mapped_column(
        Enum(TrialZoneGender, name="trial_zone_gender"),
        nullable=False,
        default=TrialZoneGender.UNISEX,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    store = relationship("Store", back_populates="trial_zones")
    studios = relationship("TrialStudio", back_populates="zone", cascade="all, delete-orphan")
    queue_tokens = relationship("TrialQueueToken", back_populates="zone")
