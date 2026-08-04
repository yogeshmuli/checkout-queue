from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.calendar import StoreCalendarDay, StoreCalendarEvent, StoreCalendarEventType, StoreHoliday
from app.models.checkout_section import CheckoutSection
from app.models.counter import Counter
from app.models.ml_model_metadata import MLModelMetadata
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

    def get_ready_ml_model_metadata(self, store_id: int) -> MLModelMetadata | None:
        statement = (
            select(MLModelMetadata)
            .where(
                MLModelMetadata.store_id == store_id,
                MLModelMetadata.status == "READY",
                MLModelMetadata.model_type == "random_forest_service_time_v2",
            )
            .order_by(MLModelMetadata.trained_at.desc().nulls_last(), MLModelMetadata.id.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def list_calendar_days(self, store_id: int) -> list[StoreCalendarDay]:
        statement = select(StoreCalendarDay).where(StoreCalendarDay.store_id == store_id).order_by(StoreCalendarDay.weekday.asc())
        return list(self.db.scalars(statement).all())

    def get_store_timezone(self, store_id: int) -> str | None:
        statement = (
            select(StoreCalendarDay.timezone)
            .where(StoreCalendarDay.store_id == store_id)
            .order_by(StoreCalendarDay.weekday.asc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def get_active_holiday(self, store_id: int, holiday_date) -> StoreHoliday | None:
        statement = select(StoreHoliday).where(
            StoreHoliday.store_id == store_id,
            StoreHoliday.holiday_date == holiday_date,
            StoreHoliday.is_active.is_(True),
        )
        return self.db.scalar(statement)

    def has_active_promotion_event(self, store_id: int, event_date) -> bool:
        statement = (
            select(StoreCalendarEvent.id)
            .where(
                StoreCalendarEvent.store_id == store_id,
                StoreCalendarEvent.event_date == event_date,
                StoreCalendarEvent.event_type.in_(
                    (
                        StoreCalendarEventType.PROMOTION,
                        StoreCalendarEventType.SALE,
                    )
                ),
                StoreCalendarEvent.is_active.is_(True),
            )
            .limit(1)
        )
        return self.db.scalar(statement) is not None

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

    def list_shared_waiting_tokens(self, store_id: int, section_id: int) -> list[QueueToken]:
        statement = (
            select(QueueToken)
            .where(
                QueueToken.store_id == store_id,
                QueueToken.section_id == section_id,
                QueueToken.assigned_counter_id.is_(None),
                QueueToken.status == QueueTokenStatus.WAITING,
            )
            .order_by(QueueToken.created_at.asc().nulls_last(), QueueToken.id.asc())
        )
        res= list(self.db.scalars(statement).all())
        return res

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

    def count_section_busy_tokens_at(
        self,
        store_id: int,
        section_id: int | None,
        at_time: datetime,
        exclude_token_id: int | None = None,
    ) -> int:
        statement = select(func.count(QueueToken.id)).where(
            QueueToken.store_id == store_id,
            QueueToken.created_at <= at_time,
            or_(QueueToken.completed_at.is_(None), QueueToken.completed_at > at_time),
            or_(QueueToken.cancelled_at.is_(None), QueueToken.cancelled_at > at_time),
        )
        if section_id is None:
            statement = statement.where(QueueToken.section_id.is_(None))
        else:
            statement = statement.where(QueueToken.section_id == section_id)
        if exclude_token_id is not None:
            statement = statement.where(QueueToken.id != exclude_token_id)
        return self.db.scalar(statement) or 0

    def count_active_counters_for_section(self, store_id: int, section_id: int | None) -> int:
        statement = (
            select(func.count(Counter.id))
            .join(CheckoutSection, CheckoutSection.id == Counter.section_id)
            .where(
                CheckoutSection.store_id == store_id,
                CheckoutSection.is_active.is_(True),
                Counter.is_active.is_(True),
            )
        )
        if section_id is not None:
            statement = statement.where(Counter.section_id == section_id)
        return self.db.scalar(statement) or 0

    def list_recent_section_terminal_tokens(
        self,
        store_id: int,
        section_id: int | None,
        start_time: datetime,
        end_time: datetime,
    ) -> list[QueueToken]:
        statement = select(QueueToken).where(
            QueueToken.store_id == store_id,
            QueueToken.status.in_(
                (
                    QueueTokenStatus.COMPLETED,
                    QueueTokenStatus.CANCELLED,
                    QueueTokenStatus.NO_SHOW,
                )
            ),
            or_(
                QueueToken.completed_at.between(start_time, end_time),
                QueueToken.cancelled_at.between(start_time, end_time),
            ),
        )
        if section_id is None:
            statement = statement.where(QueueToken.section_id.is_(None))
        else:
            statement = statement.where(QueueToken.section_id == section_id)
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

    def count_tokens_for_numbering(self, counter_id: int) -> int:
        statement = select(func.count(QueueToken.id)).where(QueueToken.assigned_counter_id == counter_id)
        return self.db.scalar(statement) or 0

    def count_shared_tokens_for_numbering(self, store_id: int, section_id: int) -> int:
        statement = select(func.count(QueueToken.id)).where(
            QueueToken.store_id == store_id,
            QueueToken.section_id == section_id,
            QueueToken.token_number.like("%-Q-%"),
        )
        return self.db.scalar(statement) or 0

    def create_token(self, token: QueueToken) -> QueueToken:
        self.db.add(token)
        self.db.flush()
        return token

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)
