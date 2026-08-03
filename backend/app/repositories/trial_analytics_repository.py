from datetime import date, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.ml_model_metadata import MLModelMetadata
from app.models.store import Store
from app.models.trial_calendar import TrialCalendarEvent
from app.models.trial_queue_token import TrialQueueToken, TrialQueueTokenStatus
from app.models.trial_studio import TrialStudio
from app.models.trial_zone import TrialZone


ACTIVE_TRIAL_TOKEN_STATUSES = (
    TrialQueueTokenStatus.WAITING,
    TrialQueueTokenStatus.CALLED,
    TrialQueueTokenStatus.SERVING,
)


class TrialAnalyticsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_store(self, store_id: int) -> Store | None:
        return self.db.get(Store, store_id)

    def list_zones(self, store_id: int) -> list[TrialZone]:
        return list(self.db.scalars(select(TrialZone).where(TrialZone.store_id == store_id).order_by(TrialZone.name, TrialZone.id)).all())

    def list_studios(self, store_id: int) -> list[TrialStudio]:
        statement = select(TrialStudio).join(TrialZone).where(TrialZone.store_id == store_id).order_by(TrialZone.name, TrialStudio.name, TrialStudio.id)
        return list(self.db.scalars(statement).all())

    def list_active_tokens(self, store_id: int) -> list[TrialQueueToken]:
        statement = select(TrialQueueToken).where(TrialQueueToken.store_id == store_id, TrialQueueToken.status.in_(ACTIVE_TRIAL_TOKEN_STATUSES)).order_by(TrialQueueToken.calling_time.asc().nulls_last(), TrialQueueToken.id)
        return list(self.db.scalars(statement).all())

    def list_tokens_since(self, store_id: int, start_at: datetime) -> list[TrialQueueToken]:
        statement = select(TrialQueueToken).where(
            TrialQueueToken.store_id == store_id,
            or_(TrialQueueToken.created_at >= start_at, TrialQueueToken.completed_at >= start_at, TrialQueueToken.cancelled_at >= start_at, TrialQueueToken.updated_at >= start_at),
        ).order_by(TrialQueueToken.created_at, TrialQueueToken.id)
        return list(self.db.scalars(statement).all())

    def list_calendar_events(self, store_id: int, start_date: date, end_date: date) -> list[TrialCalendarEvent]:
        statement = select(TrialCalendarEvent).where(
            TrialCalendarEvent.store_id == store_id,
            TrialCalendarEvent.event_date >= start_date,
            TrialCalendarEvent.event_date <= end_date,
            TrialCalendarEvent.is_active.is_(True),
        ).order_by(TrialCalendarEvent.event_date, TrialCalendarEvent.event_type)
        return list(self.db.scalars(statement).all())

    def get_latest_model_metadata(self, store_id: int) -> MLModelMetadata | None:
        statement = select(MLModelMetadata).where(
            MLModelMetadata.store_id == store_id,
            MLModelMetadata.model_type == "random_forest_trial_service_time_v1",
        ).order_by(MLModelMetadata.trained_at.desc().nulls_last(), MLModelMetadata.id.desc()).limit(1)
        return self.db.scalar(statement)
