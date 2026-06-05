from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from app.models.trial_queue_token import TrialQueueTokenStatus
from app.models.trial_zone import TrialZoneGender, TrialZoneType


class TrialQueueJoinRequest(BaseModel):
    store_id: int
    trial_zone_id: int | None = None
    phone_number: str = Field(min_length=10, max_length=10)
    item_count: int | None = Field(default=None, ge=0)
    customer_gender: TrialZoneGender | None = None
    customer_type: str | None = Field(default="regular", max_length=50)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("Phone number must contain only digits")
        return value


class TrialQueueJoinResponse(BaseModel):
    token_id: int
    token_number: str
    store_id: int
    trial_zone_id: int | None
    assigned_studio_id: int | None
    status: TrialQueueTokenStatus
    position: int
    estimated_wait_minutes: int
    calculation_method: str
    calling_time: datetime


class TrialQueueEventType(str, Enum):
    CALLED = "CALLED"
    SERVING = "SERVING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TrialQueueEventRequest(BaseModel):
    token_id: int = Field(gt=0)
    event: TrialQueueEventType
    cancellation_reason: str | None = Field(default=None, max_length=255)


class TrialTokenCancelRequest(BaseModel):
    cancellation_reason: str | None = Field(default=None, max_length=255)


class TrialQueueTokenResponse(BaseModel):
    token_id: int
    token_number: str
    store_id: int
    trial_zone_id: int | None
    assigned_studio_id: int | None
    phone_number: str
    status: TrialQueueTokenStatus
    position: int
    item_count: int | None
    customer_type: str | None
    calculation_method: str | None
    service_time_minutes: int | None
    calling_time: datetime | None
    called_at: datetime | None
    service_started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime
    cancellation_reason: str | None
    estimated_wait_minutes: int


class TrialQueueEventResponse(BaseModel):
    token_id: int
    status: TrialQueueTokenStatus
    assigned_studio_id: int | None
    called_at: datetime | None
    service_started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    calling_time: datetime | None
    estimated_wait_minutes: int


class TrialStudioQueueResponse(BaseModel):
    studio_id: int
    studio_name: str | None = None
    is_active: bool
    next_available_time: datetime
    tokens: list[TrialQueueTokenResponse]


class TrialZoneStudioQueuesResponse(BaseModel):
    zone_id: int
    zone_name: str
    store_id: int
    studios: list[TrialStudioQueueResponse]


class TrialStudioStatusUpdateRequest(BaseModel):
    is_active: bool


class TrialStoreZoneResponse(BaseModel):
    id: int
    name: str
    zone_type: TrialZoneType
    gender: TrialZoneGender


class TrialStoreResponse(BaseModel):
    id: int
    store_number: str
    name: str
    zones: list[TrialStoreZoneResponse]
