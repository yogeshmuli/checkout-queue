from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.calendar import StoreCalendarDay, StoreCalendarEvent, StoreCalendarEventType
from app.models.checkout_section import CheckoutSection
from app.models.counter import Counter
from app.models.ml_model_metadata import MLModelMetadata
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.models.store import Store


class MLRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_store_by_id(self, store_id: int) -> Store | None:
        return self.db.get(Store, store_id)

    def list_sections_for_training(self, store_id: int) -> list[CheckoutSection]:
        return list(self.db.scalars(select(CheckoutSection).where(CheckoutSection.store_id == store_id).order_by(CheckoutSection.id)).all())

    def list_counters_for_training(self, store_id: int) -> list[Counter]:
        statement = select(Counter).join(CheckoutSection).where(CheckoutSection.store_id == store_id).order_by(Counter.id)
        return list(self.db.scalars(statement).all())

    def get_section_for_training(self, section_id: int) -> CheckoutSection | None:
        return self.db.get(CheckoutSection, section_id)

    def get_counter_for_training(self, counter_id: int) -> Counter | None:
        return self.db.get(Counter, counter_id)

    def list_completed_training_tokens(self, store_id: int) -> list[QueueToken]:
        statement = (
            select(QueueToken)
            .where(
                QueueToken.store_id == store_id,
                QueueToken.status == QueueTokenStatus.COMPLETED,
                QueueToken.service_started_at.is_not(None),
                QueueToken.completed_at.is_not(None),
            )
            .order_by(QueueToken.completed_at.asc(), QueueToken.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_store_timezone(self, store_id: int) -> str | None:
        statement = (
            select(StoreCalendarDay.timezone)
            .where(StoreCalendarDay.store_id == store_id)
            .order_by(StoreCalendarDay.weekday.asc())
            .limit(1)
        )
        return self.db.scalar(statement)

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

    def get_latest_metadata(self, store_id: int, model_type: str | None = None) -> MLModelMetadata | None:
        statement = (
            select(MLModelMetadata)
            .where(MLModelMetadata.store_id == store_id)
        )
        if model_type is not None:
            statement = statement.where(MLModelMetadata.model_type == model_type)
        statement = statement.order_by(MLModelMetadata.trained_at.desc().nulls_last(), MLModelMetadata.id.desc()).limit(1)
        return self.db.scalar(statement)

    def create_metadata(self, metadata: MLModelMetadata) -> MLModelMetadata:
        self.db.add(metadata)
        self.db.flush()
        return metadata

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)
