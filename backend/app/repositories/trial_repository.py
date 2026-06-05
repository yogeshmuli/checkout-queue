from app.repositories.trial_queue_repository import ACTIVE_TRIAL_TOKEN_STATUSES, TrialQueueRepository


class TrialRepository(TrialQueueRepository):
    """Compatibility repository that exposes all Trial domain query methods."""


__all__ = ["ACTIVE_TRIAL_TOKEN_STATUSES", "TrialRepository"]
