from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.counter import Counter
from app.models.notification import NotificationLog, NotificationModuleType, NotificationType, StoreNotificationConfig
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.models.store import Store
from app.models.trial import TrialQueueToken, TrialQueueTokenStatus, TrialStudio


ACTIVE_CHECKOUT_STATUSES = (QueueTokenStatus.WAITING, QueueTokenStatus.CALLED, QueueTokenStatus.SERVING)
ACTIVE_TRIAL_STATUSES = (TrialQueueTokenStatus.WAITING, TrialQueueTokenStatus.CALLED, TrialQueueTokenStatus.SERVING)


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_store(self, store_id: int) -> Store | None:
        return self.db.get(Store, store_id)

    def get_config(self, store_id: int) -> StoreNotificationConfig | None:
        return self.db.scalar(select(StoreNotificationConfig).where(StoreNotificationConfig.store_id == store_id))

    def create_config(self, config: StoreNotificationConfig) -> StoreNotificationConfig:
        self.db.add(config)
        self.db.flush()
        return config

    def notification_exists(self, module_type: NotificationModuleType, token_id: int, notification_type: NotificationType) -> bool:
        statement = (
            select(NotificationLog.id)
            .where(
                NotificationLog.module_type == module_type,
                NotificationLog.token_id == token_id,
                NotificationLog.notification_type == notification_type,
            )
            .limit(1)
        )
        return self.db.scalar(statement) is not None

    def create_log(self, log: NotificationLog) -> NotificationLog:
        self.db.add(log)
        self.db.flush()
        return log

    def list_logs(self, store_id: int, limit: int) -> list[NotificationLog]:
        statement = (
            select(NotificationLog)
            .where(NotificationLog.store_id == store_id)
            .order_by(NotificationLog.created_at.desc(), NotificationLog.id.desc())
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def list_active_checkout_tokens(self) -> list[QueueToken]:
        statement = (
            select(QueueToken)
            .where(QueueToken.status.in_(ACTIVE_CHECKOUT_STATUSES), QueueToken.assigned_counter_id.is_not(None))
            .order_by(QueueToken.assigned_counter_id.asc(), QueueToken.calling_time.asc().nulls_last(), QueueToken.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_active_trial_tokens(self) -> list[TrialQueueToken]:
        statement = (
            select(TrialQueueToken)
            .where(TrialQueueToken.status.in_(ACTIVE_TRIAL_STATUSES), TrialQueueToken.assigned_studio_id.is_not(None))
            .order_by(TrialQueueToken.assigned_studio_id.asc(), TrialQueueToken.calling_time.asc().nulls_last(), TrialQueueToken.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_counter(self, counter_id: int) -> Counter | None:
        return self.db.get(Counter, counter_id)

    def get_studio(self, studio_id: int) -> TrialStudio | None:
        return self.db.get(TrialStudio, studio_id)

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)
