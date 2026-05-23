from datetime import date, datetime, time
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from app.models.trial import TrialCalendarEventType, TrialQueueTokenStatus, TrialStudioType, TrialZoneGender, TrialZoneType


class TrialZoneCreateRequest(BaseModel):
    store_id: int
    name: str = Field(min_length=1, max_length=100)
    zone_type: TrialZoneType = TrialZoneType.REGULAR
    gender: TrialZoneGender = TrialZoneGender.UNISEX
    is_active: bool = True


class TrialZoneUpdateRequest(BaseModel):
    store_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    zone_type: TrialZoneType | None = None
    gender: TrialZoneGender | None = None
    is_active: bool | None = None


class TrialZoneResponse(BaseModel):
    id: int
    store_id: int
    name: str
    zone_type: TrialZoneType
    gender: TrialZoneGender
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TrialStudioCreateRequest(BaseModel):
    trial_zone_id: int
    name: str | None = Field(default=None, max_length=100)
    studio_type: TrialStudioType = TrialStudioType.REGULAR
    is_active: bool = True


class TrialStudioUpdateRequest(BaseModel):
    trial_zone_id: int | None = None
    name: str | None = Field(default=None, max_length=100)
    studio_type: TrialStudioType | None = None
    is_active: bool | None = None


class TrialStudioResponse(BaseModel):
    id: int
    trial_zone_id: int
    name: str | None
    studio_type: TrialStudioType
    is_active: bool
    next_available_time: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TrialStoreConfigUpdateRequest(BaseModel):
    token_id_prefix: str | None = Field(default=None, min_length=1, max_length=20)
    base_service_minutes: int = Field(default=8, ge=0, le=240)
    per_unit_service_minutes: float = Field(default=1.0, ge=0, le=60)
    min_service_minutes: int = Field(default=10, ge=1, le=240)


class TrialStoreConfigResponse(BaseModel):
    id: int
    store_id: int
    token_id_prefix: str | None
    base_service_minutes: int
    per_unit_service_minutes: float
    min_service_minutes: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TrialCalendarDayRequest(BaseModel):
    weekday: int = Field(ge=0, le=6)
    is_open: bool = True
    open_time: time
    close_time: time


class TrialHolidayRequest(BaseModel):
    holiday_date: date
    name: str | None = Field(default=None, max_length=150)
    is_active: bool = True


class TrialCalendarEventRequest(BaseModel):
    event_date: date
    name: str | None = Field(default=None, max_length=150)
    event_type: TrialCalendarEventType
    is_active: bool = True


class TrialCalendarUpdateRequest(BaseModel):
    timezone: str = Field(default="Asia/Kolkata", min_length=1, max_length=64)
    days: list[TrialCalendarDayRequest] = Field(min_length=7, max_length=7)
    holidays: list[TrialHolidayRequest] = Field(default_factory=list)
    events: list[TrialCalendarEventRequest] | None = None


class TrialCalendarDayResponse(BaseModel):
    id: int | None = None
    weekday: int
    is_open: bool
    open_time: time
    close_time: time
    timezone: str


class TrialHolidayResponse(BaseModel):
    id: int | None = None
    holiday_date: date
    name: str | None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TrialCalendarEventResponse(BaseModel):
    id: int | None = None
    event_date: date
    name: str | None
    event_type: TrialCalendarEventType
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TrialCalendarResponse(BaseModel):
    store_id: int
    timezone: str
    days: list[TrialCalendarDayResponse]
    holidays: list[TrialHolidayResponse]
    events: list[TrialCalendarEventResponse]


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
    is_active: bool
    next_available_time: datetime
    tokens: list[TrialQueueTokenResponse]


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
