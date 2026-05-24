from datetime import date, datetime

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.ml_model_metadata import MLModelMetadata
from app.models.store import Store
from app.models.trial import (
    TrialCalendarDay,
    TrialCalendarEvent,
    TrialCalendarEventType,
    TrialHoliday,
    TrialQueueToken,
    TrialQueueTokenStatus,
    TrialStoreConfig,
    TrialStudio,
    TrialZone,
)


ACTIVE_TRIAL_TOKEN_STATUSES = (
    TrialQueueTokenStatus.WAITING,
    TrialQueueTokenStatus.CALLED,
    TrialQueueTokenStatus.SERVING,
)


class TrialRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_store(self, store_id: int) -> Store | None:
        return self.db.get(Store, store_id)

    def get_ready_trial_ml_model_metadata(self, store_id: int) -> MLModelMetadata | None:
        statement = (
            select(MLModelMetadata)
            .where(
                MLModelMetadata.store_id == store_id,
                MLModelMetadata.status == "READY",
                MLModelMetadata.model_type == "random_forest_trial_service_time_v1",
            )
            .order_by(MLModelMetadata.trained_at.desc().nulls_last(), MLModelMetadata.id.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def list_completed_trial_training_tokens(self, store_id: int) -> list[TrialQueueToken]:
        statement = (
            select(TrialQueueToken)
            .where(
                TrialQueueToken.store_id == store_id,
                TrialQueueToken.status == TrialQueueTokenStatus.COMPLETED,
                TrialQueueToken.service_started_at.is_not(None),
                TrialQueueToken.completed_at.is_not(None),
            )
            .order_by(TrialQueueToken.completed_at.asc(), TrialQueueToken.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_trial_store_timezone(self, store_id: int) -> str | None:
        statement = (
            select(TrialCalendarDay.timezone)
            .where(TrialCalendarDay.store_id == store_id)
            .order_by(TrialCalendarDay.weekday.asc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def count_trial_zone_busy_tokens_at(
        self,
        store_id: int,
        trial_zone_id: int | None,
        at_time: datetime,
        exclude_token_id: int | None = None,
    ) -> int:
        statement = select(func.count(TrialQueueToken.id)).where(
            TrialQueueToken.store_id == store_id,
            TrialQueueToken.created_at <= at_time,
            TrialQueueToken.status.in_(ACTIVE_TRIAL_TOKEN_STATUSES),
            or_(TrialQueueToken.completed_at.is_(None), TrialQueueToken.completed_at > at_time),
            or_(TrialQueueToken.cancelled_at.is_(None), TrialQueueToken.cancelled_at > at_time),
        )
        if trial_zone_id is None:
            statement = statement.where(TrialQueueToken.trial_zone_id.is_(None))
        else:
            statement = statement.where(TrialQueueToken.trial_zone_id == trial_zone_id)
        if exclude_token_id is not None:
            statement = statement.where(TrialQueueToken.id != exclude_token_id)
        return self.db.scalar(statement) or 0

    def count_active_studios_for_zone(self, store_id: int, trial_zone_id: int | None) -> int:
        statement = (
            select(func.count(TrialStudio.id))
            .join(TrialZone, TrialZone.id == TrialStudio.trial_zone_id)
            .where(
                TrialZone.store_id == store_id,
                TrialZone.is_active.is_(True),
                TrialStudio.is_active.is_(True),
            )
        )
        if trial_zone_id is not None:
            statement = statement.where(TrialStudio.trial_zone_id == trial_zone_id)
        return self.db.scalar(statement) or 0

    def list_recent_trial_zone_terminal_tokens(
        self,
        store_id: int,
        trial_zone_id: int | None,
        start_time: datetime,
        end_time: datetime,
    ) -> list[TrialQueueToken]:
        statement = select(TrialQueueToken).where(
            TrialQueueToken.store_id == store_id,
            TrialQueueToken.status.in_(
                (
                    TrialQueueTokenStatus.COMPLETED,
                    TrialQueueTokenStatus.CANCELLED,
                    TrialQueueTokenStatus.NO_SHOW,
                )
            ),
            or_(
                TrialQueueToken.completed_at.between(start_time, end_time),
                TrialQueueToken.cancelled_at.between(start_time, end_time),
            ),
        )
        if trial_zone_id is None:
            statement = statement.where(TrialQueueToken.trial_zone_id.is_(None))
        else:
            statement = statement.where(TrialQueueToken.trial_zone_id == trial_zone_id)
        return list(self.db.scalars(statement).all())

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

    def list_active_stores_with_zones(self) -> list[Store]:
        statement = (
            select(Store)
            .where(Store.is_active.is_(True))
            .options(selectinload(Store.trial_zones))
            .order_by(Store.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def create(self, instance):
        self.db.add(instance)
        self.db.flush()
        return instance

    def get_zone(self, zone_id: int) -> TrialZone | None:
        return self.db.get(TrialZone, zone_id)

    def get_zone_by_store_and_name(self, store_id: int, name: str) -> TrialZone | None:
        return self.db.scalar(select(TrialZone).where(TrialZone.store_id == store_id, TrialZone.name == name))

    def list_zones(self, include_inactive: bool = False, store_id: int | None = None) -> list[TrialZone]:
        statement = select(TrialZone).order_by(TrialZone.id.asc())
        if not include_inactive:
            statement = statement.where(TrialZone.is_active.is_(True))
        if store_id is not None:
            statement = statement.where(TrialZone.store_id == store_id)
        return list(self.db.scalars(statement).all())

    def get_studio(self, studio_id: int) -> TrialStudio | None:
        return self.db.get(TrialStudio, studio_id)

    def get_studio_by_zone_and_name(self, zone_id: int, name: str) -> TrialStudio | None:
        return self.db.scalar(select(TrialStudio).where(TrialStudio.trial_zone_id == zone_id, TrialStudio.name == name))

    def list_studios(
        self,
        include_inactive: bool = False,
        store_id: int | None = None,
        trial_zone_id: int | None = None,
    ) -> list[TrialStudio]:
        statement = select(TrialStudio).join(TrialZone, TrialZone.id == TrialStudio.trial_zone_id).order_by(TrialStudio.id.asc())
        if not include_inactive:
            statement = statement.where(TrialStudio.is_active.is_(True))
        if store_id is not None:
            statement = statement.where(TrialZone.store_id == store_id)
        if trial_zone_id is not None:
            statement = statement.where(TrialStudio.trial_zone_id == trial_zone_id)
        return list(self.db.scalars(statement).all())

    def list_active_studios(self, store_id: int, trial_zone_id: int | None) -> list[TrialStudio]:
        statement = (
            select(TrialStudio)
            .join(TrialZone, TrialZone.id == TrialStudio.trial_zone_id)
            .where(
                TrialZone.store_id == store_id,
                TrialZone.is_active.is_(True),
                TrialStudio.is_active.is_(True),
            )
        )
        if trial_zone_id is not None:
            statement = statement.where(TrialStudio.trial_zone_id == trial_zone_id)
        return list(self.db.scalars(statement).all())

    def get_config(self, store_id: int) -> TrialStoreConfig | None:
        return self.db.scalar(select(TrialStoreConfig).where(TrialStoreConfig.store_id == store_id))

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

    def get_token(self, token_id: int) -> TrialQueueToken | None:
        return self.db.get(TrialQueueToken, token_id)

    def get_latest_token_for_phone(self, store_id: int, phone_number: str) -> TrialQueueToken | None:
        return self.db.scalar(
            select(TrialQueueToken)
            .where(TrialQueueToken.store_id == store_id, TrialQueueToken.phone_number == phone_number)
            .order_by(TrialQueueToken.id.desc())
            .limit(1)
        )

    def get_active_token_for_phone(self, store_id: int, phone_number: str) -> TrialQueueToken | None:
        return self.db.scalar(
            select(TrialQueueToken).where(
                TrialQueueToken.store_id == store_id,
                TrialQueueToken.phone_number == phone_number,
                TrialQueueToken.status.in_(ACTIVE_TRIAL_TOKEN_STATUSES),
            )
        )

    def list_waiting_tokens(self, studio_id: int) -> list[TrialQueueToken]:
        return list(
            self.db.scalars(
                select(TrialQueueToken)
                .where(TrialQueueToken.assigned_studio_id == studio_id, TrialQueueToken.status == TrialQueueTokenStatus.WAITING)
                .order_by(TrialQueueToken.calling_time.asc().nulls_last(), TrialQueueToken.id.asc())
            ).all()
        )

    def get_current_serving_token(self, studio_id: int) -> TrialQueueToken | None:
        return self.db.scalar(
            select(TrialQueueToken)
            .where(TrialQueueToken.assigned_studio_id == studio_id, TrialQueueToken.status == TrialQueueTokenStatus.SERVING)
            .order_by(TrialQueueToken.service_started_at.desc().nulls_last(), TrialQueueToken.id.desc())
            .limit(1)
        )

    def get_current_called_token(self, studio_id: int) -> TrialQueueToken | None:
        return self.db.scalar(
            select(TrialQueueToken)
            .where(TrialQueueToken.assigned_studio_id == studio_id, TrialQueueToken.status == TrialQueueTokenStatus.CALLED)
            .order_by(TrialQueueToken.called_at.desc().nulls_last(), TrialQueueToken.id.desc())
            .limit(1)
        )

    def list_tokens_for_studio(self, studio_id: int) -> list[TrialQueueToken]:
        return list(
            self.db.scalars(
                select(TrialQueueToken)
                .where(TrialQueueToken.assigned_studio_id == studio_id, TrialQueueToken.status.in_(ACTIVE_TRIAL_TOKEN_STATUSES))
                .order_by(TrialQueueToken.calling_time.asc().nulls_last(), TrialQueueToken.id.asc())
            ).all()
        )

    def list_queue_tokens(
        self,
        store_id: int | None = None,
        trial_zone_id: int | None = None,
        studio_id: int | None = None,
        status: TrialQueueTokenStatus | None = None,
        include_terminal: bool = False,
    ) -> list[TrialQueueToken]:
        statement = select(TrialQueueToken)
        if store_id is not None:
            statement = statement.where(TrialQueueToken.store_id == store_id)
        if trial_zone_id is not None:
            statement = statement.where(TrialQueueToken.trial_zone_id == trial_zone_id)
        if studio_id is not None:
            statement = statement.where(TrialQueueToken.assigned_studio_id == studio_id)
        if status is not None:
            statement = statement.where(TrialQueueToken.status == status)
        elif not include_terminal:
            statement = statement.where(TrialQueueToken.status.in_(ACTIVE_TRIAL_TOKEN_STATUSES))
        return list(self.db.scalars(statement.order_by(TrialQueueToken.status.asc(), TrialQueueToken.calling_time.asc().nulls_last(), TrialQueueToken.id.asc())).all())

    def count_tokens_for_numbering(self, store_id: int, trial_zone_id: int | None) -> int:
        statement = select(func.count(TrialQueueToken.id)).where(TrialQueueToken.store_id == store_id)
        if trial_zone_id is not None:
            statement = statement.where(TrialQueueToken.trial_zone_id == trial_zone_id)
        return self.db.scalar(statement) or 0

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)

    def flush(self) -> None:
        self.db.flush()
