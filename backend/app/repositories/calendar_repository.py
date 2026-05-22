from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.calendar import StoreCalendarDay, StoreHoliday
from app.models.store import Store


class CalendarRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_store_by_id(self, store_id: int) -> Store | None:
        return self.db.get(Store, store_id)

    def list_days(self, store_id: int) -> list[StoreCalendarDay]:
        statement = select(StoreCalendarDay).where(StoreCalendarDay.store_id == store_id).order_by(StoreCalendarDay.weekday.asc())
        return list(self.db.scalars(statement).all())

    def get_day(self, store_id: int, weekday: int) -> StoreCalendarDay | None:
        statement = select(StoreCalendarDay).where(
            StoreCalendarDay.store_id == store_id,
            StoreCalendarDay.weekday == weekday,
        )
        return self.db.scalar(statement)

    def list_holidays(self, store_id: int) -> list[StoreHoliday]:
        statement = select(StoreHoliday).where(StoreHoliday.store_id == store_id).order_by(StoreHoliday.holiday_date.asc())
        return list(self.db.scalars(statement).all())

    def get_active_holiday(self, store_id: int, holiday_date: date) -> StoreHoliday | None:
        statement = select(StoreHoliday).where(
            StoreHoliday.store_id == store_id,
            StoreHoliday.holiday_date == holiday_date,
            StoreHoliday.is_active.is_(True),
        )
        return self.db.scalar(statement)

    def add(self, instance: object) -> None:
        self.db.add(instance)

    def delete_holidays(self, store_id: int) -> None:
        self.db.execute(delete(StoreHoliday).where(StoreHoliday.store_id == store_id))

    def commit(self) -> None:
        self.db.commit()

    def flush(self) -> None:
        self.db.flush()
