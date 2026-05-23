from datetime import date, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.calendar import StoreCalendarEvent
from app.models.checkout_section import CheckoutSection
from app.models.counter import Counter
from app.models.ml_model_metadata import MLModelMetadata
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.models.store import Store


ACTIVE_TOKEN_STATUSES = (
    QueueTokenStatus.WAITING,
    QueueTokenStatus.CALLED,
    QueueTokenStatus.SERVING,
)


class AnalyticsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_store(self, store_id: int) -> Store | None:
        return self.db.get(Store, store_id)

    def list_sections(self, store_id: int) -> list[CheckoutSection]:
        statement = (
            select(CheckoutSection)
            .where(CheckoutSection.store_id == store_id)
            .order_by(CheckoutSection.name.asc(), CheckoutSection.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_counters(self, store_id: int) -> list[Counter]:
        statement = (
            select(Counter)
            .join(CheckoutSection, CheckoutSection.id == Counter.section_id)
            .where(CheckoutSection.store_id == store_id)
            .order_by(CheckoutSection.name.asc(), Counter.name.asc().nulls_last(), Counter.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_active_tokens(self, store_id: int) -> list[QueueToken]:
        statement = (
            select(QueueToken)
            .where(QueueToken.store_id == store_id, QueueToken.status.in_(ACTIVE_TOKEN_STATUSES))
            .order_by(QueueToken.calling_time.asc().nulls_last(), QueueToken.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_tokens_since(self, store_id: int, start_at: datetime) -> list[QueueToken]:
        statement = (
            select(QueueToken)
            .where(
                QueueToken.store_id == store_id,
                or_(
                    QueueToken.created_at >= start_at,
                    QueueToken.completed_at >= start_at,
                    QueueToken.cancelled_at >= start_at,
                    QueueToken.updated_at >= start_at,
                ),
            )
            .order_by(QueueToken.created_at.asc(), QueueToken.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_calendar_events(self, store_id: int, start_date: date, end_date: date) -> list[StoreCalendarEvent]:
        statement = (
            select(StoreCalendarEvent)
            .where(
                StoreCalendarEvent.store_id == store_id,
                StoreCalendarEvent.event_date >= start_date,
                StoreCalendarEvent.event_date <= end_date,
                StoreCalendarEvent.is_active.is_(True),
            )
            .order_by(StoreCalendarEvent.event_date.asc(), StoreCalendarEvent.event_type.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_latest_model_metadata(self, store_id: int) -> MLModelMetadata | None:
        statement = (
            select(MLModelMetadata)
            .where(MLModelMetadata.store_id == store_id)
            .order_by(MLModelMetadata.trained_at.desc().nulls_last(), MLModelMetadata.id.desc())
            .limit(1)
        )
        return self.db.scalar(statement)
