from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models.trial import TrialQueueToken, TrialQueueTokenStatus, TrialStudio, TrialStudioType
from app.schemas.trial import TrialQueueEventRequest, TrialQueueEventType
from app.services.trial_service import TrialService


class FakeTrialRepository:
    def __init__(self, db: object) -> None:
        now = datetime.now(timezone.utc)
        self.tokens = [
            TrialQueueToken(
                id=1,
                store_id=1,
                trial_zone_id=1,
                assigned_studio_id=1,
                token_number="T-001",
                phone_number="9000000001",
                status=TrialQueueTokenStatus.WAITING,
                calling_time=now,
                service_time_minutes=10,
            )
        ]
        self.studio = TrialStudio(
            id=1,
            trial_zone_id=1,
            name="Studio 1",
            studio_type=TrialStudioType.REGULAR,
            is_active=True,
            next_available_time=now,
        )

    def get_token(self, token_id: int) -> TrialQueueToken | None:
        return next((token for token in self.tokens if token.id == token_id), None)

    def get_studio(self, studio_id: int) -> TrialStudio | None:
        return self.studio if studio_id == self.studio.id else None

    def get_current_serving_token(self, studio_id: int) -> TrialQueueToken | None:
        return next((token for token in self.tokens if token.assigned_studio_id == studio_id and token.status == TrialQueueTokenStatus.SERVING), None)

    def get_current_called_token(self, studio_id: int) -> TrialQueueToken | None:
        return next((token for token in self.tokens if token.assigned_studio_id == studio_id and token.status == TrialQueueTokenStatus.CALLED), None)

    def list_waiting_tokens(self, studio_id: int) -> list[TrialQueueToken]:
        return [
            token
            for token in self.tokens
            if token.assigned_studio_id == studio_id and token.status == TrialQueueTokenStatus.WAITING
        ]

    def commit(self) -> None:
        return None

    def refresh(self, instance: object) -> None:
        return None


@pytest.fixture
def trial_service(monkeypatch: pytest.MonkeyPatch) -> TrialService:
    fake_repository = FakeTrialRepository(None)

    def repository_factory(db: object) -> FakeTrialRepository:
        return fake_repository

    monkeypatch.setattr("app.services.trial_service.TrialRepository", repository_factory)
    return TrialService(None)


def test_called_event_rejects_already_called_trial_token(trial_service: TrialService) -> None:
    trial_service.handle_queue_event(TrialQueueEventRequest(token_id=1, event=TrialQueueEventType.CALLED))

    with pytest.raises(HTTPException) as exc_info:
        trial_service.handle_queue_event(TrialQueueEventRequest(token_id=1, event=TrialQueueEventType.CALLED))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Only waiting trial token can be called"
