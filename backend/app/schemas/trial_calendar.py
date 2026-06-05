from datetime import date, datetime, time

from pydantic import BaseModel, Field

from app.models.trial_calendar import TrialCalendarEventType


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
