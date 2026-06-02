from datetime import datetime

from pydantic import BaseModel, Field

from app.models.user import UserRole


class UserRegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=150)
    phone_number: str | None = Field(default=None, min_length=10, max_length=10)
    default_role: UserRole = UserRole.CASHIER
    store_id: int | None = None
    section_id: int | None = None
    assigned_counter_id: int | None = None
    assigned_zone_id: int | None = None


class UserLoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone_number: str | None
    default_role: UserRole
    store_id: int | None
    section_id: int | None
    assigned_counter_id: int | None
    assigned_zone_id: int | None
    is_active: bool
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


class LogoutRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str
