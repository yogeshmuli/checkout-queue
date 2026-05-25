from enum import Enum
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from app.models.checkout_section import CheckoutSectionType
from app.models.queue_token import QueueTokenStatus


class QueueJoinRequest(BaseModel):
    store_id: int
    section_id: int | None = None
    phone_number: str = Field(min_length=10, max_length=10)
    item_count: int | None = Field(default=None, ge=0)
    basket_size: str | None = Field(default=None, max_length=50)
    cart_type: str | None = Field(default=None, max_length=50)
    is_still_shopping: bool = False
    customer_type: str | None = Field(default="regular", max_length=50)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("Phone number must contain only digits")
        return value


class QueueJoinResponse(BaseModel):
    token_id: int
    token_number: str
    store_id: int
    section_id: int | None
    assigned_counter_id: int | None
    status: QueueTokenStatus
    position: int = Field(description="Computed queue position at join time; not persisted in queue_tokens table")
    estimated_wait_minutes: int = Field(description="Computed from calling_time and current server time")
    calculation_method: str
    calling_time: datetime


class QueueEventType(str, Enum):
    CALLED = "CALLED"
    SERVING = "SERVING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class QueueEventRequest(BaseModel):
    token_id: int = Field(gt=0)
    event: QueueEventType
    cancellation_reason: str | None = Field(default=None, max_length=255)


class QueueEventResponse(BaseModel):
    token_id: int
    status: QueueTokenStatus
    assigned_counter_id: int | None
    called_at: datetime | None
    service_started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    calling_time: datetime | None
    estimated_wait_minutes: int


class QueueTokenResponse(BaseModel):
    token_id: int
    token_number: str
    store_id: int
    section_id: int | None
    assigned_counter_id: int | None
    phone_number: str
    status: QueueTokenStatus
    position: int
    item_count: int | None
    basket_size: str | None
    cart_type: str | None
    customer_type: str | None
    calculation_method: str | None
    service_time_minutes: int | None
    calling_time: datetime | None
    called_at: datetime | None
    service_started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    estimated_wait_minutes: int


class CounterQueueResponse(BaseModel):
    counter_id: int
    counter_name: str | None = None
    is_active: bool
    next_available_time: datetime
    tokens: list[QueueTokenResponse]


class CounterStatusUpdateRequest(BaseModel):
    is_active: bool


class TokenCancelRequest(BaseModel):
    cancellation_reason: str | None = Field(default=None, max_length=255)


class QueueStoreSectionResponse(BaseModel):
    id: int
    name: str
    section_type: CheckoutSectionType


class QueueStoreResponse(BaseModel):
    id: int
    store_number: str
    name: str
    sections: list[QueueStoreSectionResponse]
