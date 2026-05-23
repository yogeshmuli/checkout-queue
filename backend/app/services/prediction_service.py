import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import joblib

from app.models.ml_model_metadata import MLModelMetadata
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.schemas.ml import ServiceTimePredictionRequest, ServiceTimePredictionResponse


DEFAULT_TIMEZONE = "Asia/Kolkata"
RECENT_HISTORY_DAYS = 7


class PredictionRepository(Protocol):
    def get_ready_ml_model_metadata(self, store_id: int) -> MLModelMetadata | None:
        ...

    def get_store_timezone(self, store_id: int) -> str | None:
        ...

    def count_section_busy_tokens_at(
        self,
        store_id: int,
        section_id: int | None,
        at_time: datetime,
        exclude_token_id: int | None = None,
    ) -> int:
        ...

    def count_active_counters_for_section(self, store_id: int, section_id: int | None) -> int:
        ...

    def list_recent_section_terminal_tokens(
        self,
        store_id: int,
        section_id: int | None,
        start_time: datetime,
        end_time: datetime,
    ) -> list[QueueToken]:
        ...

    def has_active_promotion_event(self, store_id: int, event_date) -> bool:
        ...


class PredictionService:
    _artifact_cache: dict[tuple[int, str, str, float], object] = {}

    def __init__(self, repository: PredictionRepository) -> None:
        self.repository = repository

    def predict_service_time(
        self,
        store_id: int,
        payload: ServiceTimePredictionRequest,
    ) -> ServiceTimePredictionResponse | None:
        metadata = self.repository.get_ready_ml_model_metadata(store_id)
        if metadata is None or not metadata.artifact_path:
            return None

        artifact_path = Path(metadata.artifact_path)
        if not artifact_path.exists():
            return None
        cache_key = self._cache_key(store_id, metadata, artifact_path)

        if metadata.model_type == "linear_service_time_v1" or artifact_path.suffix == ".json":
            artifact = self._load_json_artifact(cache_key, artifact_path)
            if artifact is None:
                return None
            return self._predict_linear_json(metadata, artifact, payload)

        try:
            artifact = self._load_joblib_artifact(cache_key, artifact_path)
            if not isinstance(artifact, dict):
                return None
            model = artifact["model"]
            features = self._build_features(store_id, payload)
            predicted = float(model.predict([features])[0])
            service_time_minutes = max(1, min(240, math.ceil(predicted)))
        except (OSError, KeyError, TypeError, ValueError, AttributeError):
            return None

        return ServiceTimePredictionResponse(
            service_time_minutes=service_time_minutes,
            calculation_method="ML_PREDICTED",
            model_version=metadata.model_version,
        )

    def _predict_linear_json(
        self,
        metadata: MLModelMetadata,
        artifact: dict[str, object],
        payload: ServiceTimePredictionRequest,
    ) -> ServiceTimePredictionResponse | None:
        try:
            item_count = payload.item_count or 0
            predicted = artifact["intercept"] + (artifact["item_count_slope"] * item_count)
            service_time_minutes = max(1, min(240, math.ceil(predicted)))
        except (KeyError, TypeError, ValueError):
            return None

        return ServiceTimePredictionResponse(
            service_time_minutes=service_time_minutes,
            calculation_method="ML_PREDICTED",
            model_version=metadata.model_version,
        )

    def _cache_key(
        self,
        store_id: int,
        metadata: MLModelMetadata,
        artifact_path: Path,
    ) -> tuple[int, str, str, float]:
        return (
            store_id,
            metadata.model_version,
            str(artifact_path),
            artifact_path.stat().st_mtime,
        )

    def _load_json_artifact(self, cache_key: tuple[int, str, str, float], artifact_path: Path) -> dict[str, object] | None:
        cached_artifact = self._artifact_cache.get(cache_key)
        if isinstance(cached_artifact, dict):
            return cached_artifact

        try:
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        self._artifact_cache[cache_key] = artifact
        return artifact

    def _load_joblib_artifact(self, cache_key: tuple[int, str, str, float], artifact_path: Path) -> object | None:
        cached_artifact = self._artifact_cache.get(cache_key)
        if cached_artifact is not None:
            return cached_artifact

        try:
            artifact = joblib.load(artifact_path)
        except (OSError, ValueError):
            return None

        self._artifact_cache[cache_key] = artifact
        return artifact

    def _build_features(self, store_id: int, payload: ServiceTimePredictionRequest) -> dict[str, int | float | str]:
        reference_time = self._normalize_to_utc(payload.requested_at or datetime.now(timezone.utc))
        timezone_name = self.repository.get_store_timezone(store_id) or DEFAULT_TIMEZONE
        local_time = reference_time.astimezone(self._timezone_or_default(timezone_name))
        recent_tokens = self.repository.list_recent_section_terminal_tokens(
            store_id=store_id,
            section_id=payload.section_id,
            start_time=reference_time - timedelta(days=RECENT_HISTORY_DAYS),
            end_time=reference_time,
        )
        terminal_count = len(recent_tokens)
        cancelled_count = len(
            [
                token
                for token in recent_tokens
                if token.status in (QueueTokenStatus.CANCELLED, QueueTokenStatus.NO_SHOW)
            ]
        )
        recent_completed_durations = [
            (token.completed_at - token.service_started_at).total_seconds() / 60
            for token in recent_tokens
            if token.status == QueueTokenStatus.COMPLETED
            and token.service_started_at is not None
            and token.completed_at is not None
            and token.completed_at > token.service_started_at
        ]

        return {
            "item_count": float(payload.item_count or 0),
            "section_busy_count_at_join": float(
                self.repository.count_section_busy_tokens_at(store_id, payload.section_id, reference_time)
            ),
            "section_active_counter_count_at_join": float(
                self.repository.count_active_counters_for_section(store_id, payload.section_id)
            ),
            "recent_cancellation_rate": (cancelled_count / terminal_count) if terminal_count else 0.0,
            "recent_average_service_minutes": (
                sum(recent_completed_durations) / len(recent_completed_durations) if recent_completed_durations else 0.0
            ),
            "hour_of_day": float(local_time.hour),
            "day_of_week": float(local_time.weekday()),
            "is_weekend": 1.0 if local_time.weekday() >= 5 else 0.0,
            "promotion_day_flag": 1.0 if self.repository.has_active_promotion_event(store_id, local_time.date()) else 0.0,
            "basket_size": (payload.basket_size or "unknown").lower(),
            "cart_type": (payload.cart_type or "unknown").lower(),
            "customer_type": (payload.customer_type or "unknown").lower(),
            "section_id": str(payload.section_id or "none"),
            "assigned_counter_id": str(payload.assigned_counter_id or "none"),
        }

    def _normalize_to_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _timezone_or_default(self, timezone_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            return ZoneInfo(DEFAULT_TIMEZONE)
