from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.calendar import StoreCalendarDay, StoreHoliday
from app.models.checkout_section import CheckoutSection
from app.models.counter import Counter
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.models.store import Store
from app.models.store_config import StoreConfig


ACTIVE_TOKEN_STATUSES = (
    QueueTokenStatus.WAITING,
    QueueTokenStatus.CALLED,
    QueueTokenStatus.SERVING,
)


class QueueRepository:
    def list_active_counters(self, store_id: int, section_id: int | None) -> list[Counter]:
        statement = (
            select(Counter)
            .join(CheckoutSection, CheckoutSection.id == Counter.section_id)
            .where(
                CheckoutSection.store_id == store_id,
                CheckoutSection.is_active.is_(True),
                Counter.is_active.is_(True),
            )
        )
        if section_id is not None:
            statement = statement.where(Counter.section_id == section_id)
        return list(self.db.scalars(statement).all())  
    
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_store(self, store_id: int) -> Store | None:
        return self.db.get(Store, store_id)

    def get_store_config(self, store_id: int) -> StoreConfig | None:
        statement = select(StoreConfig).where(StoreConfig.store_id == store_id)
        return self.db.scalar(statement)

    def list_calendar_days(self, store_id: int) -> list[StoreCalendarDay]:
        statement = select(StoreCalendarDay).where(StoreCalendarDay.store_id == store_id).order_by(StoreCalendarDay.weekday.asc())
        return list(self.db.scalars(statement).all())

    def get_active_holiday(self, store_id: int, holiday_date) -> StoreHoliday | None:
        statement = select(StoreHoliday).where(
            StoreHoliday.store_id == store_id,
            StoreHoliday.holiday_date == holiday_date,
            StoreHoliday.is_active.is_(True),
        )
        return self.db.scalar(statement)

    def list_active_stores_with_sections(self) -> list[Store]:
        statement = (
            select(Store)
            .where(Store.is_active.is_(True))
            .options(selectinload(Store.checkout_sections))
            .order_by(Store.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_section(self, section_id: int) -> CheckoutSection | None:
        return self.db.get(CheckoutSection, section_id)

    def get_counter(self, counter_id: int) -> Counter | None:
        return self.db.get(Counter, counter_id)

    def get_token(self, token_id: int) -> QueueToken | None:
        return self.db.get(QueueToken, token_id)

    def get_latest_token_for_phone(self, store_id: int, phone_number: str) -> QueueToken | None:
        statement = (
            select(QueueToken)
            .where(
                QueueToken.store_id == store_id,
                QueueToken.phone_number == phone_number,
            )
            .order_by(QueueToken.id.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def get_latest_token_by_phone(self, phone_number: str) -> QueueToken | None:
        statement = (
            select(QueueToken)
            .where(QueueToken.phone_number == phone_number)
            .order_by(QueueToken.id.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def get_active_token_for_phone(self, store_id: int, phone_number: str) -> QueueToken | None:
        statement = select(QueueToken).where(
            QueueToken.store_id == store_id,
            QueueToken.phone_number == phone_number,
            QueueToken.status.in_(ACTIVE_TOKEN_STATUSES),
        )
        return self.db.scalar(statement)

    def list_waiting_tokens(self, counter_id: int) -> list[QueueToken]:
        statement = (
            select(QueueToken)
            .where(
                QueueToken.assigned_counter_id == counter_id,
                QueueToken.status == QueueTokenStatus.WAITING,
            )
            .order_by(QueueToken.calling_time.asc().nulls_last(), QueueToken.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_active_tokens_for_counter(self, counter_id: int) -> list[QueueToken]:
        statement = (
            select(QueueToken)
            .where(
                QueueToken.assigned_counter_id == counter_id,
                QueueToken.status.in_(ACTIVE_TOKEN_STATUSES),
            )
            .order_by(QueueToken.calling_time.asc().nulls_last(), QueueToken.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_tokens_for_counter(self, counter_id: int) -> list[QueueToken]:
        statement = (
            select(QueueToken)
            .where(
                QueueToken.assigned_counter_id == counter_id,
                QueueToken.status.in_(
                    (
                        QueueTokenStatus.WAITING,
                        QueueTokenStatus.CALLED,
                        QueueTokenStatus.SERVING,
                    )
                ),
            )
            .order_by(QueueToken.calling_time.asc().nulls_last(), QueueToken.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_queue_tokens(
        self,
        store_id: int | None = None,
        section_id: int | None = None,
        counter_id: int | None = None,
        status: QueueTokenStatus | None = None,
        include_terminal: bool = False,
    ) -> list[QueueToken]:
        statement = select(QueueToken)
        if store_id is not None:
            statement = statement.where(QueueToken.store_id == store_id)
        if section_id is not None:
            statement = statement.where(QueueToken.section_id == section_id)
        if counter_id is not None:
            statement = statement.where(QueueToken.assigned_counter_id == counter_id)
        if status is not None:
            statement = statement.where(QueueToken.status == status)
        elif not include_terminal:
            statement = statement.where(QueueToken.status.in_(ACTIVE_TOKEN_STATUSES))

        statement = statement.order_by(
            QueueToken.status.asc(),
            QueueToken.calling_time.asc().nulls_last(),
            QueueToken.id.asc(),
        )
        return list(self.db.scalars(statement).all())

    def get_current_serving_customer_for_counter(self, counter_id: int) -> QueueToken | None:
        statement = (
            select(QueueToken)
            .where(
                QueueToken.assigned_counter_id == counter_id,
                QueueToken.status == QueueTokenStatus.SERVING,
            )
            .order_by(QueueToken.service_started_at.desc().nulls_last(), QueueToken.id.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def get_current_called_customer_for_counter(self, counter_id: int) -> QueueToken | None:
        statement = (
            select(QueueToken)
            .where(
                QueueToken.assigned_counter_id == counter_id,
                QueueToken.status == QueueTokenStatus.CALLED,
            )
            .order_by(QueueToken.called_at.desc().nulls_last(), QueueToken.id.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def count_tokens_for_numbering(self, store_id: int, section_id: int | None) -> int:
        statement = select(func.count(QueueToken.id)).where(QueueToken.store_id == store_id)
        if section_id is not None:
            statement = statement.where(QueueToken.section_id == section_id)
        return self.db.scalar(statement) or 0

    def create_token(self, token: QueueToken) -> QueueToken:
        self.db.add(token)
        self.db.flush()
        return token

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)
