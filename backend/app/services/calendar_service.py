from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.calendar import StoreCalendarDay, StoreHoliday
from app.repositories.calendar_repository import CalendarRepository
from app.schemas.calendar import (
    StoreCalendarDayResponse,
    StoreCalendarResponse,
    StoreCalendarUpdateRequest,
    StoreHolidayResponse,
)


DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_OPEN_TIME = time(0, 0)
DEFAULT_CLOSE_TIME = time(23, 59)


class CalendarService:
    def __init__(self, db: Session) -> None:
        self.repository = CalendarRepository(db)

    def get_calendar(self, store_id: int) -> StoreCalendarResponse:
        self._ensure_store_exists(store_id)
        days = self._ensure_default_days(store_id)
        holidays = self.repository.list_holidays(store_id)
        self.repository.commit()
        return self._build_response(store_id, days, holidays)

    def update_calendar(self, store_id: int, payload: StoreCalendarUpdateRequest) -> StoreCalendarResponse:
        self._ensure_store_exists(store_id)
        self._validate_timezone(payload.timezone)

        weekdays = [day.weekday for day in payload.days]
        if len(set(weekdays)) != 7 or set(weekdays) != set(range(7)):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Calendar must include weekdays 0 through 6")

        for day_payload in payload.days:
            day = self.repository.get_day(store_id, day_payload.weekday)
            if day is None:
                day = StoreCalendarDay(store_id=store_id, weekday=day_payload.weekday)
                self.repository.add(day)
            day.is_open = day_payload.is_open
            day.open_time = day_payload.open_time
            day.close_time = day_payload.close_time
            day.timezone = payload.timezone

        self.repository.delete_holidays(store_id)
        for holiday_payload in payload.holidays:
            self.repository.add(
                StoreHoliday(
                    store_id=store_id,
                    holiday_date=holiday_payload.holiday_date,
                    name=holiday_payload.name.strip() if holiday_payload.name else None,
                    is_active=holiday_payload.is_active,
                )
            )

        self.repository.commit()
        return self._build_response(store_id, self.repository.list_days(store_id), self.repository.list_holidays(store_id))

    def is_store_open_for_queue(self, store_id: int, now: datetime | None = None) -> bool:
        now_utc = now or datetime.now(timezone.utc)
        days = self.repository.list_days(store_id)
        if not days:
            return True

        timezone_name = days[0].timezone or DEFAULT_TIMEZONE
        store_tz = self._timezone_or_default(timezone_name)
        local_now = now_utc.astimezone(store_tz)

        if self.repository.get_active_holiday(store_id, local_now.date()) is not None:
            return False

        day = next((calendar_day for calendar_day in days if calendar_day.weekday == local_now.weekday()), None)
        if day is None:
            return True
        if not day.is_open:
            return False

        local_time = local_now.time().replace(tzinfo=None)
        if day.open_time <= day.close_time:
            return day.open_time <= local_time <= day.close_time
        return local_time >= day.open_time or local_time <= day.close_time

    def _ensure_store_exists(self, store_id: int) -> None:
        store = self.repository.get_store_by_id(store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    def _ensure_default_days(self, store_id: int) -> list[StoreCalendarDay]:
        days = self.repository.list_days(store_id)
        if days:
            return days

        created_days = [
            StoreCalendarDay(
                store_id=store_id,
                weekday=weekday,
                is_open=True,
                open_time=DEFAULT_OPEN_TIME,
                close_time=DEFAULT_CLOSE_TIME,
                timezone=DEFAULT_TIMEZONE,
            )
            for weekday in range(7)
        ]
        for day in created_days:
            self.repository.add(day)
        self.repository.flush()
        return created_days

    def _build_response(
        self,
        store_id: int,
        days: list[StoreCalendarDay],
        holidays: list[StoreHoliday],
    ) -> StoreCalendarResponse:
        timezone_name = days[0].timezone if days else DEFAULT_TIMEZONE
        return StoreCalendarResponse(
            store_id=store_id,
            timezone=timezone_name,
            days=[
                StoreCalendarDayResponse(
                    id=day.id,
                    weekday=day.weekday,
                    is_open=day.is_open,
                    open_time=day.open_time,
                    close_time=day.close_time,
                    timezone=day.timezone,
                )
                for day in sorted(days, key=lambda calendar_day: calendar_day.weekday)
            ],
            holidays=[
                StoreHolidayResponse(
                    id=holiday.id,
                    holiday_date=holiday.holiday_date,
                    name=holiday.name,
                    is_active=holiday.is_active,
                    created_at=holiday.created_at,
                    updated_at=holiday.updated_at,
                )
                for holiday in holidays
            ],
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
