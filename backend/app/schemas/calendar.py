from datetime import date, datetime, time

from pydantic import BaseModel, Field


class StoreCalendarDayRequest(BaseModel):
    weekday: int = Field(ge=0, le=6)
    is_open: bool = True
    open_time: time
    close_time: time


class StoreHolidayRequest(BaseModel):
    holiday_date: date
    name: str | None = Field(default=None, max_length=150)
    is_active: bool = True


class StoreCalendarUpdateRequest(BaseModel):
    timezone: str = Field(default="Asia/Kolkata", min_length=1, max_length=64)
    days: list[StoreCalendarDayRequest] = Field(min_length=7, max_length=7)
    holidays: list[StoreHolidayRequest] = Field(default_factory=list)


class StoreCalendarDayResponse(BaseModel):
    id: int | None = None
    weekday: int
    is_open: bool
    open_time: time
    close_time: time
    timezone: str


class StoreHolidayResponse(BaseModel):
    id: int | None = None
    holiday_date: date
    name: str | None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class StoreCalendarResponse(BaseModel):
    store_id: int
    timezone: str
    days: list[StoreCalendarDayResponse]
    holidays: list[StoreHolidayResponse]
