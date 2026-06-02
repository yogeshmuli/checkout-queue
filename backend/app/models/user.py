import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    STORE_ADMIN = "STORE_ADMIN"
    MANAGER = "MANAGER"
    CASHIER = "CASHIER"
    SUPPORT = "SUPPORT"
    TRIAL_ZONE_ASSISTANT = "TRIAL_ZONE_ASSISTANT"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int | None] = mapped_column(ForeignKey("stores.id", ondelete="SET NULL"), index=True)
    section_id: Mapped[int | None] = mapped_column(ForeignKey("checkout_sections.id", ondelete="SET NULL"), index=True)
    assigned_counter_id: Mapped[int | None] = mapped_column(ForeignKey("counters.id", ondelete="SET NULL"), index=True)
    assigned_zone_id: Mapped[int | None] = mapped_column(ForeignKey("trial_zones.id", ondelete="SET NULL"), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(10), unique=True, index=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    default_role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    store = relationship("Store")
    section = relationship("CheckoutSection")
    assigned_counter = relationship("Counter", back_populates="assigned_users")
    assigned_zone = relationship("TrialZone")
    store_access = relationship("UserStoreAccess", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class UserStoreAccess(TimestampMixin, Base):
    __tablename__ = "user_store_access"
    __table_args__ = (UniqueConstraint("user_id", "store_id", name="uq_user_store_access_user_store"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    user = relationship("User", back_populates="store_access")
    store = relationship("Store")


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="refresh_tokens")
