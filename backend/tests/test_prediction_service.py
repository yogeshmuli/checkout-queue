from datetime import datetime, timedelta, timezone

import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import Pipeline

from app.models.ml_model_metadata import MLModelMetadata
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.schemas.ml import ServiceTimePredictionRequest
from app.services.prediction_service import PredictionService


class FakePredictionRepository:
    def __init__(self, artifact_path: str | None) -> None:
        self.metadata = (
            MLModelMetadata(
                store_id=1,
                model_type="random_forest_service_time_v2",
                model_version="service-time-test",
                status="READY",
                artifact_path=artifact_path,
                sample_size=2,
            )
            if artifact_path
            else None
        )

    def get_ready_ml_model_metadata(self, store_id: int) -> MLModelMetadata | None:
        return self.metadata

    def get_store_timezone(self, store_id: int) -> str:
        return "UTC"

    def count_section_busy_tokens_at(self, store_id: int, section_id: int | None, at_time: datetime, exclude_token_id: int | None = None) -> int:
        return 3

    def count_active_counters_for_section(self, store_id: int, section_id: int | None) -> int:
        return 2

    def list_recent_section_terminal_tokens(
        self,
        store_id: int,
        section_id: int | None,
        start_time: datetime,
        end_time: datetime,
    ) -> list[QueueToken]:
        service_started_at = end_time - timedelta(minutes=20)
        return [
            QueueToken(
                store_id=store_id,
                section_id=section_id,
                token_number="T-1",
                phone_number="9876543210",
                status=QueueTokenStatus.COMPLETED,
                service_started_at=service_started_at,
                completed_at=service_started_at + timedelta(minutes=6),
            ),
            QueueToken(
                store_id=store_id,
                section_id=section_id,
                token_number="T-2",
                phone_number="9876543211",
                status=QueueTokenStatus.CANCELLED,
                cancelled_at=end_time - timedelta(minutes=5),
            ),
        ]

    def has_active_promotion_event(self, store_id: int, event_date) -> bool:
        return True


def create_test_artifact(tmp_path):
    model = Pipeline(
        steps=[
            ("features", DictVectorizer(sparse=False)),
            ("regressor", RandomForestRegressor(n_estimators=10, random_state=42)),
        ]
    )
    training_features = [
        {
            "item_count": 1.0,
            "section_busy_count_at_join": 0.0,
            "section_active_counter_count_at_join": 1.0,
            "recent_cancellation_rate": 0.0,
            "recent_average_service_minutes": 4.0,
            "hour_of_day": 10.0,
            "day_of_week": 1.0,
            "is_weekend": 0.0,
            "promotion_day_flag": 0.0,
            "basket_size": "small",
            "cart_type": "basket",
            "customer_type": "regular",
            "section_id": "1",
            "assigned_counter_id": "1",
        },
        {
            "item_count": 20.0,
            "section_busy_count_at_join": 3.0,
            "section_active_counter_count_at_join": 2.0,
            "recent_cancellation_rate": 0.5,
            "recent_average_service_minutes": 7.0,
            "hour_of_day": 18.0,
            "day_of_week": 5.0,
            "is_weekend": 1.0,
            "promotion_day_flag": 1.0,
            "basket_size": "large",
            "cart_type": "cart",
            "customer_type": "regular",
            "section_id": "1",
            "assigned_counter_id": "2",
        },
    ]
    model.fit(training_features, [4.0, 12.0])
    artifact_path = tmp_path / "model.joblib"
    joblib.dump({"model": model}, artifact_path)
    return artifact_path


def test_prediction_service_loads_random_forest_artifact(tmp_path) -> None:
    PredictionService._artifact_cache.clear()
    artifact_path = create_test_artifact(tmp_path)
    prediction = PredictionService(FakePredictionRepository(str(artifact_path))).predict_service_time(
        1,
        ServiceTimePredictionRequest(
            section_id=1,
            assigned_counter_id=2,
            item_count=15,
            basket_size="large",
            cart_type="cart",
            customer_type="regular",
            requested_at=datetime(2026, 5, 22, 18, 0, tzinfo=timezone.utc),
        ),
    )

    assert prediction is not None
    assert prediction.calculation_method == "ML_PREDICTED"
    assert prediction.model_version == "service-time-test"
    assert prediction.service_time_minutes > 0


def test_prediction_service_reuses_cached_artifact(tmp_path, monkeypatch) -> None:
    PredictionService._artifact_cache.clear()
    artifact_path = create_test_artifact(tmp_path)
    original_load = joblib.load
    load_count = 0

    def counting_load(path):
        nonlocal load_count
        load_count += 1
        return original_load(path)

    monkeypatch.setattr("app.services.prediction_service.joblib.load", counting_load)
    service = PredictionService(FakePredictionRepository(str(artifact_path)))
    payload = ServiceTimePredictionRequest(
        section_id=1,
        assigned_counter_id=2,
        item_count=15,
        basket_size="large",
        cart_type="cart",
        customer_type="regular",
        requested_at=datetime(2026, 5, 22, 18, 0, tzinfo=timezone.utc),
    )

    first_prediction = service.predict_service_time(1, payload)
    second_prediction = service.predict_service_time(1, payload)

    assert first_prediction is not None
    assert second_prediction is not None
    assert load_count == 1


def test_prediction_service_returns_none_without_ready_model() -> None:
    PredictionService._artifact_cache.clear()
    prediction = PredictionService(FakePredictionRepository(None)).predict_service_time(
        1,
        ServiceTimePredictionRequest(item_count=3),
    )

    assert prediction is None
