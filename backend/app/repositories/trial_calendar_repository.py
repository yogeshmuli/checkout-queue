from datetime import date, datetime

from sqlalchemy import delete, select

from app.models.trial_calendar import TrialCalendarDay, TrialCalendarEvent, TrialCalendarEventType, TrialHoliday
from app.repositories.trial_base_repository import TrialBaseRepository


class TrialCalendarRepository(TrialBaseRepository):
    def get_trial_store_timezone(self, store_id: int) -> str | None:
        statement = (
            select(TrialCalendarDay.timezone)
            .where(TrialCalendarDay.store_id == store_id)
            .order_by(TrialCalendarDay.weekday.asc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def has_active_trial_promotion_event(self, store_id: int, event_date: date) -> bool:
        statement = (
            select(TrialCalendarEvent.id)
            .where(
                TrialCalendarEvent.store_id == store_id,
                TrialCalendarEvent.event_date == event_date,
                TrialCalendarEvent.event_type.in_((TrialCalendarEventType.PROMOTION, TrialCalendarEventType.SALE)),
                TrialCalendarEvent.is_active.is_(True),
            )
            .limit(1)
        )
        return self.db.scalar(statement) is not None

    def list_days(self, store_id: int) -> list[TrialCalendarDay]:
        return list(self.db.scalars(select(TrialCalendarDay).where(TrialCalendarDay.store_id == store_id).order_by(TrialCalendarDay.weekday.asc())).all())

    def get_day(self, store_id: int, weekday: int) -> TrialCalendarDay | None:
        return self.db.scalar(select(TrialCalendarDay).where(TrialCalendarDay.store_id == store_id, TrialCalendarDay.weekday == weekday))

    def list_holidays(self, store_id: int) -> list[TrialHoliday]:
        return list(self.db.scalars(select(TrialHoliday).where(TrialHoliday.store_id == store_id).order_by(TrialHoliday.holiday_date.asc())).all())

    def get_active_holiday(self, store_id: int, holiday_date: date) -> TrialHoliday | None:
        return self.db.scalar(select(TrialHoliday).where(TrialHoliday.store_id == store_id, TrialHoliday.holiday_date == holiday_date, TrialHoliday.is_active.is_(True)))

    def list_events(self, store_id: int) -> list[TrialCalendarEvent]:
        return list(self.db.scalars(select(TrialCalendarEvent).where(TrialCalendarEvent.store_id == store_id).order_by(TrialCalendarEvent.event_date.asc())).all())

    def delete_holidays(self, store_id: int) -> None:
        self.db.execute(delete(TrialHoliday).where(TrialHoliday.store_id == store_id))

    def delete_events(self, store_id: int) -> None:
        self.db.execute(delete(TrialCalendarEvent).where(TrialCalendarEvent.store_id == store_id))
