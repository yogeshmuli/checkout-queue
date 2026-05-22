from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.user import UserRole


class StaffCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=150)
    phone_number: str | None = Field(default=None, min_length=10, max_length=10)
    default_role: UserRole = UserRole.CASHIER
    store_id: int | None = None
    section_id: int | None = None
    assigned_counter_id: int | None = None
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str | None) -> str | None:
        if value is not None and not value.isdigit():
            raise ValueError("Phone number must contain only digits")
        return value

    @field_validator("default_role")
    @classmethod
    def validate_staff_role(cls, value: UserRole) -> UserRole:
        if value == UserRole.SUPER_ADMIN:
            raise ValueError("SUPER_ADMIN cannot be managed through staff APIs")
        return value


class StaffUpdateRequest(BaseModel):
    email: str | None = Field(default=None, min_length=3, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone_number: str | None = Field(default=None, min_length=10, max_length=10)
    default_role: UserRole | None = None
    store_id: int | None = None
    section_id: int | None = None
    assigned_counter_id: int | None = None
    is_active: bool | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        return value.lower() if value is not None else value

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str | None) -> str | None:
        if value is not None and not value.isdigit():
            raise ValueError("Phone number must contain only digits")
        return value

    @field_validator("default_role")
    @classmethod
    def validate_staff_role(cls, value: UserRole | None) -> UserRole | None:
        if value == UserRole.SUPER_ADMIN:
            raise ValueError("SUPER_ADMIN cannot be managed through staff APIs")
        return value


class StaffResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone_number: str | None
    default_role: UserRole
    store_id: int | None
    section_id: int | None
    assigned_counter_id: int | None
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
