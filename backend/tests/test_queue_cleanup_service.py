from datetime import datetime, timedelta, timezone

from app.models.counter import Counter, CounterType
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.models.trial_queue_token import TrialQueueToken, TrialQueueTokenStatus
from app.models.trial_studio import TrialStudio, TrialStudioType
from app.services.queue_cleanup_service import NIGHTLY_CLEANUP_REASON, QueueCleanupService


class FakeQueueCleanupRepository:
    def __init__(self, db: object) -> None:
        self.checkout_tokens = [
            QueueToken(
                id=1,
                store_id=1,
                token_number="C-001",
                phone_number="9000000001",
                status=QueueTokenStatus.WAITING,
            ),
            QueueToken(
                id=2,
                store_id=1,
                token_number="C-002",
                phone_number="9000000002",
                status=QueueTokenStatus.SERVING,
            ),
        ]
        self.trial_tokens = [
            TrialQueueToken(
                id=1,
                store_id=1,
                token_number="T-001",
                phone_number="9000000003",
                status=TrialQueueTokenStatus.CALLED,
            )
        ]
        self.counters = [
            Counter(
                id=1,
                section_id=1,
                counter_type=CounterType.REGULAR,
                next_available_time=datetime.now(timezone.utc) + timedelta(hours=2),
            )
        ]
        self.studios = [
            TrialStudio(
                id=1,
                trial_zone_id=1,
                studio_type=TrialStudioType.REGULAR,
                next_available_time=datetime.now(timezone.utc) + timedelta(hours=3),
            )
        ]
        self.committed = False

    def list_active_checkout_tokens(self) -> list[QueueToken]:
        return [token for token in self.checkout_tokens if token.status in (QueueTokenStatus.WAITING, QueueTokenStatus.CALLED, QueueTokenStatus.SERVING)]

    def list_active_trial_tokens(self) -> list[TrialQueueToken]:
        return [
            token
            for token in self.trial_tokens
            if token.status in (TrialQueueTokenStatus.WAITING, TrialQueueTokenStatus.CALLED, TrialQueueTokenStatus.SERVING)
        ]

    def list_checkout_counters(self) -> list[Counter]:
        return self.counters

    def list_trial_studios(self) -> list[TrialStudio]:
        return self.studios

    def commit(self) -> None:
        self.committed = True


def test_nightly_cleanup_cancels_active_tokens_and_resets_availability(monkeypatch) -> None:
    fake_repository = FakeQueueCleanupRepository(None)

    def repository_factory(db: object) -> FakeQueueCleanupRepository:
        return fake_repository

    monkeypatch.setattr("app.services.queue_cleanup_service.QueueCleanupRepository", repository_factory)
    service = QueueCleanupService(None)
    ran_at = datetime(2026, 5, 24, 18, 35, tzinfo=timezone.utc)

    result = service.run_nightly_cleanup(ran_at=ran_at)

    assert result.checkout_tokens_cancelled == 2
    assert result.trial_tokens_cancelled == 1
    assert result.checkout_counters_reset == 1
    assert result.trial_studios_reset == 1
    assert fake_repository.committed is True
    assert all(token.status == QueueTokenStatus.CANCELLED for token in fake_repository.checkout_tokens)
    assert all(token.cancelled_at == ran_at for token in fake_repository.checkout_tokens)
    assert all(token.cancellation_reason == NIGHTLY_CLEANUP_REASON for token in fake_repository.checkout_tokens)
    assert all(token.status == TrialQueueTokenStatus.CANCELLED for token in fake_repository.trial_tokens)
    assert fake_repository.counters[0].next_available_time == ran_at
    assert fake_repository.studios[0].next_available_time == ran_at
