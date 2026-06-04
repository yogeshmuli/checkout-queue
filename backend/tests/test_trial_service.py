from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.models.trial import TrialQueueToken, TrialQueueTokenStatus, TrialStoreConfig, TrialStudio, TrialStudioType, TrialZone
from app.models.user import User, UserRole
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
                created_at=now,
                updated_at=now,
            )
        ]
        self.zones = {
            1: TrialZone(id=1, store_id=1, name="Zone 1"),
            2: TrialZone(id=2, store_id=2, name="Zone 2"),
        }
        self.studios = {
            1: TrialStudio(id=1, trial_zone_id=1, name="Studio 1", studio_type=TrialStudioType.REGULAR, is_active=True, next_available_time=now),
            2: TrialStudio(id=2, trial_zone_id=1, name="Studio 2", studio_type=TrialStudioType.REGULAR, is_active=False, next_available_time=now),
            3: TrialStudio(id=3, trial_zone_id=2, name="Studio 3", studio_type=TrialStudioType.REGULAR, is_active=True, next_available_time=now),
        }
        self.configs = {
            1: TrialStoreConfig(store_id=1, token_id_prefix="TR", base_service_minutes=8, per_unit_service_minutes=1.2, min_service_minutes=10)
        }

    def get_token(self, token_id: int) -> TrialQueueToken | None:
        return next((token for token in self.tokens if token.id == token_id), None)

    def get_studio(self, studio_id: int) -> TrialStudio | None:
        return self.studios.get(studio_id)

    def get_zone(self, zone_id: int) -> TrialZone | None:
        return self.zones.get(zone_id)

    def list_studios(self, include_inactive: bool = False, store_id: int | None = None, trial_zone_id: int | None = None) -> list[TrialStudio]:
        studios = list(self.studios.values())
        if not include_inactive:
            studios = [studio for studio in studios if studio.is_active]
        if trial_zone_id is not None:
            studios = [studio for studio in studios if studio.trial_zone_id == trial_zone_id]
        return studios

    def list_tokens_for_studio(self, studio_id: int) -> list[TrialQueueToken]:
        return [
            token
            for token in self.tokens
            if token.assigned_studio_id == studio_id and token.status in (TrialQueueTokenStatus.WAITING, TrialQueueTokenStatus.CALLED, TrialQueueTokenStatus.SERVING)
        ]

    def get_current_serving_token(self, studio_id: int) -> TrialQueueToken | None:
        return next((token for token in self.tokens if token.assigned_studio_id == studio_id and token.status == TrialQueueTokenStatus.SERVING), None)

    def get_current_called_token(self, studio_id: int) -> TrialQueueToken | None:
        return next((token for token in self.tokens if token.assigned_studio_id == studio_id and token.status == TrialQueueTokenStatus.CALLED), None)

    def list_waiting_tokens(self, studio_id: int) -> list[TrialQueueToken]:
        waiting = [
            token
            for token in self.tokens
            if token.assigned_studio_id == studio_id and token.status == TrialQueueTokenStatus.WAITING
        ]
        max_dt = datetime.max.replace(tzinfo=timezone.utc)
        return sorted(waiting, key=lambda token: ((token.calling_time or max_dt), token.id or 0))

    def get_config(self, store_id: int) -> TrialStoreConfig | None:
        return self.configs.get(store_id)

    def count_tokens_for_numbering(self, store_id: int, trial_zone_id: int | None) -> int:
        return len(
            [
                token
                for token in self.tokens
                if token.store_id == store_id and token.trial_zone_id == trial_zone_id
            ]
        )

    def create(self, instance):
        if getattr(instance, "id", None) is None:
            instance.id = max((token.id for token in self.tokens), default=0) + 1
        self.tokens.append(instance)
        return instance

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


def test_zone_summary_returns_active_and_inactive_studios(trial_service: TrialService) -> None:
    assistant = User(default_role=UserRole.TRIAL_ZONE_ASSISTANT, assigned_zone_id=1)

    response = trial_service.get_zone_studio_queues(1, current_user=assistant)

    assert response.zone_id == 1
    assert [studio.studio_id for studio in response.studios] == [1, 2]


def test_trial_assistant_cannot_access_studio_outside_zone(trial_service: TrialService) -> None:
    assistant = User(default_role=UserRole.TRIAL_ZONE_ASSISTANT, assigned_zone_id=1)

    with pytest.raises(HTTPException) as exc_info:
        trial_service.get_studio_queue(3, current_user=assistant)

    assert exc_info.value.status_code == 403


def test_trial_assistant_cannot_start_token_outside_zone(trial_service: TrialService) -> None:
    trial_service.repository.tokens.append(
        TrialQueueToken(
            id=2,
            store_id=2,
            trial_zone_id=2,
            assigned_studio_id=3,
            token_number="T-002",
            phone_number="9000000002",
            status=TrialQueueTokenStatus.WAITING,
            calling_time=datetime.now(timezone.utc),
            service_time_minutes=10,
        )
    )
    assistant = User(default_role=UserRole.TRIAL_ZONE_ASSISTANT, assigned_zone_id=1)

    with pytest.raises(HTTPException) as exc_info:
        trial_service.start_token(2, current_user=assistant)

    assert exc_info.value.status_code == 403


def test_manager_can_access_zone_inside_assigned_store(trial_service: TrialService) -> None:
    manager = User(default_role=UserRole.MANAGER, store_id=1)

    response = trial_service.get_zone_studio_queues(1, current_user=manager)

    assert response.zone_id == 1


def test_manager_cannot_access_zone_outside_assigned_store(trial_service: TrialService) -> None:
    manager = User(default_role=UserRole.MANAGER, store_id=1)

    with pytest.raises(HTTPException) as exc_info:
        trial_service.get_zone_studio_queues(2, current_user=manager)

    assert exc_info.value.status_code == 403


def test_trial_customer_cancel_allows_waiting_and_called_tokens(trial_service: TrialService) -> None:
    called_token = TrialQueueToken(
        id=2,
        store_id=1,
        trial_zone_id=1,
        assigned_studio_id=1,
        token_number="T-002",
        phone_number="9000000002",
        status=TrialQueueTokenStatus.CALLED,
        calling_time=datetime.now(timezone.utc),
        called_at=datetime.now(timezone.utc),
        service_time_minutes=10,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    trial_service.repository.tokens.append(called_token)

    waiting_response = trial_service.cancel_token_by_customer(1)
    called_response = trial_service.cancel_token_by_customer(2)

    assert waiting_response.status == TrialQueueTokenStatus.CANCELLED
    assert called_response.status == TrialQueueTokenStatus.CANCELLED
    assert trial_service.repository.tokens[0].cancellation_reason == "Cancelled by customer"
    assert called_token.cancellation_reason == "Cancelled by customer"


def test_trial_customer_cancel_rejects_serving_and_terminal_tokens(trial_service: TrialService) -> None:
    token = trial_service.repository.tokens[0]
    token.status = TrialQueueTokenStatus.SERVING

    with pytest.raises(HTTPException) as serving_exc:
        trial_service.cancel_token_by_customer(token.id)

    token.status = TrialQueueTokenStatus.COMPLETED

    with pytest.raises(HTTPException) as terminal_exc:
        trial_service.cancel_token_by_customer(token.id)

    assert serving_exc.value.status_code == 409
    assert terminal_exc.value.status_code == 409


def test_trial_customer_move_last_cancels_original_and_creates_replacement_in_same_studio(trial_service: TrialService) -> None:
    now = datetime.now(timezone.utc)
    second_token = TrialQueueToken(
        id=2,
        store_id=1,
        trial_zone_id=1,
        assigned_studio_id=1,
        token_number="T-002",
        phone_number="9000000002",
        status=TrialQueueTokenStatus.WAITING,
        calling_time=now + timedelta(minutes=10),
        service_time_minutes=12,
        created_at=now,
        updated_at=now,
    )
    trial_service.repository.tokens.append(second_token)

    replacement = trial_service.move_token_last_by_customer(1)
    original = trial_service.repository.get_token(1)
    replacement_token = trial_service.repository.get_token(replacement.token_id)

    assert original.status == TrialQueueTokenStatus.CANCELLED
    assert original.cancellation_reason == "Moved to end by customer"
    assert replacement.status == TrialQueueTokenStatus.WAITING
    assert replacement.assigned_studio_id == original.assigned_studio_id
    assert replacement.phone_number == original.phone_number
    assert replacement.item_count == original.item_count
    assert replacement.token_id != original.id
    assert replacement_token.calling_time > second_token.calling_time
    assert trial_service.repository.studios[1].next_available_time > replacement_token.calling_time


def test_trial_customer_move_last_rejects_serving_terminal_missing_and_unassigned_tokens(trial_service: TrialService) -> None:
    token = trial_service.repository.tokens[0]
    token.status = TrialQueueTokenStatus.SERVING

    with pytest.raises(HTTPException) as serving_exc:
        trial_service.move_token_last_by_customer(token.id)

    token.status = TrialQueueTokenStatus.CANCELLED

    with pytest.raises(HTTPException) as terminal_exc:
        trial_service.move_token_last_by_customer(token.id)

    unassigned = TrialQueueToken(
        id=99,
        store_id=1,
        trial_zone_id=1,
        assigned_studio_id=None,
        token_number="UNASSIGNED",
        phone_number="9000000099",
        status=TrialQueueTokenStatus.WAITING,
        calling_time=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    trial_service.repository.tokens.append(unassigned)

    with pytest.raises(HTTPException) as unassigned_exc:
        trial_service.move_token_last_by_customer(unassigned.id)

    with pytest.raises(HTTPException) as missing_exc:
        trial_service.move_token_last_by_customer(404)

    assert serving_exc.value.status_code == 409
    assert terminal_exc.value.status_code == 409
    assert unassigned_exc.value.status_code == 409
    assert missing_exc.value.status_code == 404
