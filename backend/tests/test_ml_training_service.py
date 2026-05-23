from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.models.queue_token import QueueToken, QueueTokenStatus
from app.models.store import Store
from app.services.ml_training_service import MLTrainingService


class FakeMLRepository:
    def __init__(self, db: object) -> None:
        self.stores = {1: Store(id=1, store_number="STORE-001", name="Main Store", is_active=True)}
        self.tokens: list[QueueToken] = []
        self.metadata = []

    def get_store_by_id(self, store_id: int) -> Store | None:
        return self.stores.get(store_id)

    def list_completed_training_tokens(self, store_id: int) -> list[QueueToken]:
        return [token for token in self.tokens if token.store_id == store_id]

    def get_latest_metadata(self, store_id: int):
        return self.metadata[-1] if self.metadata else None

    def get_store_timezone(self, store_id: int) -> str:
        return "Asia/Kolkata"

    def count_section_busy_tokens_at(self, store_id: int, section_id: int | None, at_time: datetime, exclude_token_id: int | None = None) -> int:
        return len(
            [
                token
                for token in self.tokens
                if token.store_id == store_id
                and token.section_id == section_id
                and token.id != exclude_token_id
                and token.created_at is not None
                and token.created_at <= at_time
                and (token.completed_at is None or token.completed_at > at_time)
                and (token.cancelled_at is None or token.cancelled_at > at_time)
            ]
        )

    def count_active_counters_for_section(self, store_id: int, section_id: int | None) -> int:
        return 2

    def list_recent_section_terminal_tokens(
        self,
        store_id: int,
        section_id: int | None,
        start_time: datetime,
        end_time: datetime,
    ) -> list[QueueToken]:
        terminal_statuses = {
            QueueTokenStatus.COMPLETED,
            QueueTokenStatus.CANCELLED,
            QueueTokenStatus.NO_SHOW,
        }
        return [
            token
            for token in self.tokens
            if token.store_id == store_id
            and token.section_id == section_id
            and token.status in terminal_statuses
            and (
                (token.completed_at is not None and start_time <= token.completed_at <= end_time)
                or (token.cancelled_at is not None and start_time <= token.cancelled_at <= end_time)
            )
        ]

    def has_active_promotion_event(self, store_id: int, event_date) -> bool:
        return event_date.day == 15

    def create_metadata(self, metadata):
        metadata.id = len(self.metadata) + 1
        self.metadata.append(metadata)
        return metadata

    def commit(self) -> None:
        return None

    def refresh(self, instance: object) -> None:
        return None


@pytest.fixture
def ml_service(monkeypatch: pytest.MonkeyPatch, tmp_path) -> MLTrainingService:
    fake_repository = FakeMLRepository(None)

    def repository_factory(db: object) -> FakeMLRepository:
        return fake_repository

    monkeypatch.setattr("app.services.ml_training_service.MLRepository", repository_factory)
    monkeypatch.setattr("app.services.ml_training_service.settings.ML_MODEL_DIR", str(tmp_path))
    monkeypatch.setattr("app.services.ml_training_service.settings.ML_MIN_TRAINING_SAMPLES", 3)
    return MLTrainingService(None)


def test_train_store_model_rejects_insufficient_data(ml_service: MLTrainingService) -> None:
    with pytest.raises(HTTPException) as exc_info:
        ml_service.train_store_model(1)

    assert exc_info.value.status_code == 422


def test_train_store_model_creates_metadata_and_artifact(ml_service: MLTrainingService) -> None:
    now = datetime.now(timezone.utc)
    for index in range(3):
        started_at = now + timedelta(minutes=index)
        ml_service.repository.tokens.append(
            QueueToken(
                id=index + 1,
                store_id=1,
                section_id=1,
                assigned_counter_id=1,
                token_number=f"T-{index + 1}",
                phone_number=f"987654321{index}",
                status=QueueTokenStatus.COMPLETED,
                item_count=index + 1,
                basket_size="medium",
                cart_type="basket",
                customer_type="regular",
                created_at=started_at - timedelta(minutes=10),
                service_started_at=started_at,
                completed_at=started_at + timedelta(minutes=5 + index),
            )
        )

    metadata = ml_service.train_store_model(1)
    stored_metadata = ml_service.repository.metadata[0]

    assert metadata.status == "READY"
    assert metadata.sample_size == 3
    assert metadata.mae is not None
    assert metadata.model_type == "random_forest_service_time_v2"
    assert metadata.feature_importance is not None
    assert "item_count" in metadata.feature_importance
    assert stored_metadata.artifact_path.endswith(".joblib")
