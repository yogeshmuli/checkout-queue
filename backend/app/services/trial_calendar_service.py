from datetime import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.trial_calendar import TrialCalendarDay, TrialCalendarEvent, TrialHoliday
from app.repositories.trial_calendar_repository import TrialCalendarRepository
from app.schemas.trial_calendar import (
    TrialCalendarDayResponse,
    TrialCalendarEventResponse,
    TrialCalendarResponse,
    TrialCalendarUpdateRequest,
    TrialHolidayResponse,
)


DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_OPEN_TIME = time(0, 0)
DEFAULT_CLOSE_TIME = time(23, 59)


class TrialCalendarService:
    def __init__(self, db: Session) -> None:
        self.repository = TrialCalendarRepository(db)

    def get_calendar(self, store_id: int) -> TrialCalendarResponse:
        self._ensure_store_exists(store_id)
        days = self._ensure_default_days(store_id)
        self.repository.commit()
        return self._build_calendar_response(store_id, days, self.repository.list_holidays(store_id), self.repository.list_events(store_id))

    def update_calendar(self, store_id: int, payload: TrialCalendarUpdateRequest) -> TrialCalendarResponse:
        self._ensure_store_exists(store_id)
        self._validate_timezone(payload.timezone)
        weekdays = [day.weekday for day in payload.days]
        if len(set(weekdays)) != 7 or set(weekdays) != set(range(7)):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Trial calendar must include weekdays 0 through 6")
        for day_payload in payload.days:
            day = self.repository.get_day(store_id, day_payload.weekday)
            if day is None:
                day = TrialCalendarDay(store_id=store_id, weekday=day_payload.weekday)
                self.repository.create(day)
            day.is_open = day_payload.is_open
            day.open_time = day_payload.open_time
            day.close_time = day_payload.close_time
            day.timezone = payload.timezone
        self.repository.delete_holidays(store_id)
        for holiday_payload in payload.holidays:
            self.repository.create(TrialHoliday(store_id=store_id, holiday_date=holiday_payload.holiday_date, name=holiday_payload.name, is_active=holiday_payload.is_active))
        if payload.events is not None:
            self.repository.delete_events(store_id)
            for event_payload in payload.events:
                self.repository.create(TrialCalendarEvent(store_id=store_id, event_date=event_payload.event_date, name=event_payload.name, event_type=event_payload.event_type, is_active=event_payload.is_active))
        self.repository.commit()
        return self._build_calendar_response(store_id, self.repository.list_days(store_id), self.repository.list_holidays(store_id), self.repository.list_events(store_id))

    def _ensure_store_exists(self, store_id: int) -> None:
        if self.repository.get_store(store_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    def _ensure_default_days(self, store_id: int) -> list[TrialCalendarDay]:
        days = self.repository.list_days(store_id)
        if days:
            return days
        days = [TrialCalendarDay(store_id=store_id, weekday=weekday, is_open=True, open_time=DEFAULT_OPEN_TIME, close_time=DEFAULT_CLOSE_TIME, timezone=DEFAULT_TIMEZONE) for weekday in range(7)]
        for day in days:
            self.repository.create(day)
        self.repository.flush()
        return days

    def _build_calendar_response(self, store_id, days, holidays, events) -> TrialCalendarResponse:
        return TrialCalendarResponse(
            store_id=store_id,
            timezone=days[0].timezone if days else DEFAULT_TIMEZONE,
            days=[TrialCalendarDayResponse(id=day.id, weekday=day.weekday, is_open=day.is_open, open_time=day.open_time, close_time=day.close_time, timezone=day.timezone) for day in sorted(days, key=lambda day: day.weekday)],
            holidays=[TrialHolidayResponse(id=holiday.id, holiday_date=holiday.holiday_date, name=holiday.name, is_active=holiday.is_active, created_at=holiday.created_at, updated_at=holiday.updated_at) for holiday in holidays],
            events=[TrialCalendarEventResponse(id=event.id, event_date=event.event_date, name=event.name, event_type=event.event_type, is_active=event.is_active, created_at=event.created_at, updated_at=event.updated_at) for event in events],
        )

    def _validate_timezone(self, timezone_name: str) -> None:
        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid timezone") from exc

    def _timezone_or_default(self, timezone_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            return ZoneInfo(DEFAULT_TIMEZONE)
