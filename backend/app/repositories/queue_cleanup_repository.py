from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.counter import Counter
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.models.trial_queue_token import TrialQueueToken, TrialQueueTokenStatus
from app.models.trial_studio import TrialStudio


ACTIVE_CHECKOUT_STATUSES = (
    QueueTokenStatus.WAITING,
    QueueTokenStatus.CALLED,
    QueueTokenStatus.SERVING,
)

ACTIVE_TRIAL_STATUSES = (
    TrialQueueTokenStatus.WAITING,
    TrialQueueTokenStatus.CALLED,
    TrialQueueTokenStatus.SERVING,
)


class QueueCleanupRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_active_checkout_tokens(self) -> list[QueueToken]:
        statement = select(QueueToken).where(QueueToken.status.in_(ACTIVE_CHECKOUT_STATUSES))
        return list(self.db.scalars(statement).all())

    def list_active_trial_tokens(self) -> list[TrialQueueToken]:
        statement = select(TrialQueueToken).where(TrialQueueToken.status.in_(ACTIVE_TRIAL_STATUSES))
        return list(self.db.scalars(statement).all())

    def list_checkout_counters(self) -> list[Counter]:
        return list(self.db.scalars(select(Counter)).all())

    def list_trial_studios(self) -> list[TrialStudio]:
        return list(self.db.scalars(select(TrialStudio)).all())

    def commit(self) -> None:
        self.db.commit()
