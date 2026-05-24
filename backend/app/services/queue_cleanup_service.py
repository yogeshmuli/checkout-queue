from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.queue_token import QueueTokenStatus
from app.models.trial import TrialQueueTokenStatus
from app.repositories.queue_cleanup_repository import QueueCleanupRepository


NIGHTLY_CLEANUP_REASON = "Nightly queue cleanup"


@dataclass(frozen=True)
class QueueCleanupResult:
    checkout_tokens_cancelled: int
    trial_tokens_cancelled: int
    checkout_counters_reset: int
    trial_studios_reset: int
    ran_at: datetime


class QueueCleanupService:
    def __init__(self, db: Session) -> None:
        self.repository = QueueCleanupRepository(db)

    def run_nightly_cleanup(self, ran_at: datetime | None = None) -> QueueCleanupResult:
        cleanup_time = self._normalize_to_utc(ran_at or datetime.now(timezone.utc))

        checkout_tokens = self.repository.list_active_checkout_tokens()
        for token in checkout_tokens:
            token.status = QueueTokenStatus.CANCELLED
            token.cancelled_at = cleanup_time
            token.cancellation_reason = NIGHTLY_CLEANUP_REASON

        trial_tokens = self.repository.list_active_trial_tokens()
        for token in trial_tokens:
            token.status = TrialQueueTokenStatus.CANCELLED
            token.cancelled_at = cleanup_time
            token.cancellation_reason = NIGHTLY_CLEANUP_REASON

        checkout_counters = self.repository.list_checkout_counters()
        for counter in checkout_counters:
            counter.next_available_time = cleanup_time

        trial_studios = self.repository.list_trial_studios()
        for studio in trial_studios:
            studio.next_available_time = cleanup_time

        self.repository.commit()

        return QueueCleanupResult(
            checkout_tokens_cancelled=len(checkout_tokens),
            trial_tokens_cancelled=len(trial_tokens),
            checkout_counters_reset=len(checkout_counters),
            trial_studios_reset=len(trial_studios),
            ran_at=cleanup_time,
        )

    def _normalize_to_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
