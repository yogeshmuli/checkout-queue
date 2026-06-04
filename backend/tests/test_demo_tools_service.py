from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.checkout_section import CheckoutSection
from app.models.counter import Counter
from app.models.ml_model_metadata import MLModelMetadata
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.models.store import Store
from app.models.user import User, UserRole
from app.routes.demo_tools_routes import router as demo_tools_router
from app.models.trial import TrialQueueToken, TrialQueueTokenStatus, TrialStudio, TrialZone
from app.routes.api import api_router
from app.services.demo_tools_service import (
    CHECKOUT_COMPLETED_SAMPLE_COUNT,
    CHECKOUT_WAITING_SAMPLE_COUNT,
    DEMO_STORE_NUMBER,
    TRIAL_COMPLETED_SAMPLE_COUNT,
    TRIAL_WAITING_SAMPLE_COUNT,
    DemoToolsService,
)


class FakeDemoToolsRepository:
    def __init__(self, db: object) -> None:
        self.stores: dict[int, Store] = {}
        self.sections: list[CheckoutSection] = []
        self.counters: list[Counter] = []
        self.zones: list[TrialZone] = []
        self.studios: list[TrialStudio] = []
        self.checkout_tokens: list[QueueToken] = []
        self.trial_tokens: list[TrialQueueToken] = []
        self.metadata: list[MLModelMetadata] = []
        self.next_id = 1
        self.committed = False

    def _assign_id(self, instance) -> None:
        if getattr(instance, "id", None) is None:
            instance.id = self.next_id
            self.next_id += 1

    def get_store_by_number(self, store_number: str) -> Store | None:
        return next((store for store in self.stores.values() if store.store_number == store_number), None)

    def create(self, instance):
        self._assign_id(instance)
        if isinstance(instance, Store):
            self.stores[instance.id] = instance
        elif isinstance(instance, CheckoutSection):
            self.sections.append(instance)
        elif isinstance(instance, Counter):
            self.counters.append(instance)
        elif isinstance(instance, TrialZone):
            self.zones.append(instance)
        elif isinstance(instance, TrialStudio):
            self.studios.append(instance)
        elif isinstance(instance, QueueToken):
            self.checkout_tokens.append(instance)
        elif isinstance(instance, TrialQueueToken):
            self.trial_tokens.append(instance)
        elif isinstance(instance, MLModelMetadata):
            self.metadata.append(instance)
        return instance

    def checkout_section_for_store(self, store_id: int) -> CheckoutSection | None:
        return next((section for section in self.sections if section.store_id == store_id), None)

    def checkout_counters_for_store(self, store_id: int) -> list[Counter]:
        section_ids = {section.id for section in self.sections if section.store_id == store_id}
        return [counter for counter in self.counters if counter.section_id in section_ids]

    def trial_zone_for_store(self, store_id: int) -> TrialZone | None:
        return next((zone for zone in self.zones if zone.store_id == store_id), None)

    def trial_studios_for_store(self, store_id: int) -> list[TrialStudio]:
        zone_ids = {zone.id for zone in self.zones if zone.store_id == store_id}
        return [studio for studio in self.studios if studio.trial_zone_id in zone_ids]

    def count_checkout_completed_tokens(self, store_id: int) -> int:
        return len([token for token in self.checkout_tokens if token.store_id == store_id and token.status == QueueTokenStatus.COMPLETED])

    def count_checkout_terminal_tokens(self, store_id: int) -> int:
        return len(
            [
                token
                for token in self.checkout_tokens
                if token.store_id == store_id and token.status in (QueueTokenStatus.COMPLETED, QueueTokenStatus.CANCELLED, QueueTokenStatus.NO_SHOW)
            ]
        )

    def count_checkout_waiting_tokens(self, store_id: int) -> int:
        return len([token for token in self.checkout_tokens if token.store_id == store_id and token.status == QueueTokenStatus.WAITING])

    def count_trial_completed_tokens(self, store_id: int) -> int:
        return len([token for token in self.trial_tokens if token.store_id == store_id and token.status == TrialQueueTokenStatus.COMPLETED])

    def count_trial_terminal_tokens(self, store_id: int) -> int:
        return len(
            [
                token
                for token in self.trial_tokens
                if token.store_id == store_id and token.status in (TrialQueueTokenStatus.COMPLETED, TrialQueueTokenStatus.CANCELLED, TrialQueueTokenStatus.NO_SHOW)
            ]
        )

    def count_trial_waiting_tokens(self, store_id: int) -> int:
        return len([token for token in self.trial_tokens if token.store_id == store_id and token.status == TrialQueueTokenStatus.WAITING])

    def count_ml_metadata(self, store_id: int) -> int:
        return len([metadata for metadata in self.metadata if metadata.store_id == store_id])

    def delete_ml_metadata(self, store_id: int) -> None:
        self.metadata = [metadata for metadata in self.metadata if metadata.store_id != store_id]

    def delete_store(self, store: Store) -> None:
        self.stores.pop(store.id, None)
        self.sections = [section for section in self.sections if section.store_id != store.id]
        section_ids = {section.id for section in self.sections}
        self.counters = [counter for counter in self.counters if counter.section_id in section_ids]
        self.zones = [zone for zone in self.zones if zone.store_id != store.id]
        zone_ids = {zone.id for zone in self.zones}
        self.studios = [studio for studio in self.studios if studio.trial_zone_id in zone_ids]
        self.checkout_tokens = [token for token in self.checkout_tokens if token.store_id != store.id]
        self.trial_tokens = [token for token in self.trial_tokens if token.store_id != store.id]

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        return None

    def refresh(self, instance: object) -> None:
        return None


@pytest.fixture
def demo_service(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> DemoToolsService:
    fake_repository = FakeDemoToolsRepository(None)

    def repository_factory(db: object) -> FakeDemoToolsRepository:
        return fake_repository

    monkeypatch.setattr("app.services.demo_tools_service.DemoToolsRepository", repository_factory)
    monkeypatch.setattr(settings, "ML_MODEL_DIR", str(tmp_path))
    return DemoToolsService(None)


def test_demo_tools_routes_are_not_registered_by_default() -> None:
    paths = {route.path for route in api_router.routes}

    assert "/demotools/ml-training-data" not in paths


def test_demo_tools_routes_reject_non_super_admin() -> None:
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(demo_tools_router)
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[get_current_user] = lambda: User(
        id=1,
        email="manager@example.com",
        full_name="Manager",
        password_hash="hash",
        default_role=UserRole.MANAGER,
        is_active=True,
    )

    response = TestClient(app).get("/demotools/ml-training-data/status")

    assert response.status_code == 403


def test_seed_creates_checkout_and_trial_training_data(demo_service: DemoToolsService) -> None:
    response = demo_service.seed_ml_training_data()
    status_response = demo_service.get_ml_training_data_status()

    assert response.exists is True
    assert response.store_number == DEMO_STORE_NUMBER
    assert response.ids.store_id is not None
    assert response.ids.checkout_section_id is not None
    assert len(response.ids.checkout_counter_ids) == 3
    assert response.ids.trial_zone_id is not None
    assert len(response.ids.trial_studio_ids) == 3
    assert response.counts.checkout_completed_tokens == CHECKOUT_COMPLETED_SAMPLE_COUNT
    assert response.counts.trial_completed_tokens == TRIAL_COMPLETED_SAMPLE_COUNT
    assert response.counts.checkout_waiting_tokens == CHECKOUT_WAITING_SAMPLE_COUNT
    assert response.counts.trial_waiting_tokens == TRIAL_WAITING_SAMPLE_COUNT
    assert response.counts.checkout_terminal_tokens > response.counts.checkout_completed_tokens
    assert response.counts.trial_terminal_tokens > response.counts.trial_completed_tokens
    assert status_response.counts.checkout_waiting_tokens == CHECKOUT_WAITING_SAMPLE_COUNT
    assert status_response.counts.trial_waiting_tokens == TRIAL_WAITING_SAMPLE_COUNT


def test_seed_anchors_waiting_queues_to_one_current_timestamp(demo_service: DemoToolsService, monkeypatch: pytest.MonkeyPatch) -> None:
    seeded_at = datetime(2026, 6, 2, 12, 30, tzinfo=timezone.utc)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return seeded_at

    monkeypatch.setattr("app.services.demo_tools_service.datetime", FixedDateTime)
    demo_service.seed_ml_training_data()

    checkout_waiting = [token for token in demo_service.repository.checkout_tokens if token.status == QueueTokenStatus.WAITING]
    trial_waiting = [token for token in demo_service.repository.trial_tokens if token.status == TrialQueueTokenStatus.WAITING]

    assert len(checkout_waiting) == CHECKOUT_WAITING_SAMPLE_COUNT
    assert len(trial_waiting) == TRIAL_WAITING_SAMPLE_COUNT
    assert {token.created_at for token in checkout_waiting + trial_waiting} == {seeded_at}
    assert all(token.calling_time >= seeded_at for token in checkout_waiting + trial_waiting)
    assert all(
        counter.next_available_time >= token.calling_time + timedelta(minutes=token.service_time_minutes)
        for counter in demo_service.repository.counters
        for token in checkout_waiting
        if token.assigned_counter_id == counter.id
    )
    assert all(
        studio.next_available_time >= token.calling_time + timedelta(minutes=token.service_time_minutes)
        for studio in demo_service.repository.studios
        for token in trial_waiting
        if token.assigned_studio_id == studio.id
    )


def test_seed_rejects_existing_demo_store_without_replace(demo_service: DemoToolsService) -> None:
    demo_service.seed_ml_training_data()

    with pytest.raises(HTTPException) as exc_info:
        demo_service.seed_ml_training_data()

    assert exc_info.value.status_code == 409


def test_seed_replace_recreates_demo_data(demo_service: DemoToolsService) -> None:
    first = demo_service.seed_ml_training_data()
    second = demo_service.seed_ml_training_data(replace=True)

    assert first.ids.store_id != second.ids.store_id
    assert second.counts.checkout_completed_tokens == CHECKOUT_COMPLETED_SAMPLE_COUNT
    assert second.counts.trial_completed_tokens == TRIAL_COMPLETED_SAMPLE_COUNT
    assert second.counts.checkout_waiting_tokens == CHECKOUT_WAITING_SAMPLE_COUNT
    assert second.counts.trial_waiting_tokens == TRIAL_WAITING_SAMPLE_COUNT


def test_cleanup_removes_store_metadata_and_artifacts(demo_service: DemoToolsService) -> None:
    seeded = demo_service.seed_ml_training_data()
    store_id = seeded.ids.store_id
    assert store_id is not None
    demo_service.repository.create(MLModelMetadata(store_id=store_id, model_type="demo", model_version="demo"))
    checkout_artifact_dir = Path(settings.ML_MODEL_DIR) / f"store_{store_id}"
    trial_artifact_dir = Path(settings.ML_MODEL_DIR) / f"trial_store_{store_id}"
    checkout_artifact_dir.mkdir(parents=True)
    trial_artifact_dir.mkdir(parents=True)

    response = demo_service.clean_ml_training_data()
    status_response = demo_service.get_ml_training_data_status()

    assert response.exists is False
    assert response.counts.ml_metadata_rows == 1
    assert response.counts.checkout_waiting_tokens == CHECKOUT_WAITING_SAMPLE_COUNT
    assert response.counts.trial_waiting_tokens == TRIAL_WAITING_SAMPLE_COUNT
    assert status_response.exists is False
    assert not checkout_artifact_dir.exists()
    assert not trial_artifact_dir.exists()


def test_cleanup_is_safe_when_demo_store_is_missing(demo_service: DemoToolsService) -> None:
    response = demo_service.clean_ml_training_data()

    assert response.exists is False
    assert response.counts.checkout_completed_tokens == 0
