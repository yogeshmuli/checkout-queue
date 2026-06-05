import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import joblib

from app.models.ml_model_metadata import MLModelMetadata
from app.models.trial_queue_token import TrialQueueToken, TrialQueueTokenStatus
from app.schemas.ml import ServiceTimePredictionResponse, TrialServiceTimePredictionRequest


DEFAULT_TIMEZONE = "Asia/Kolkata"
RECENT_HISTORY_DAYS = 7


class TrialPredictionRepository(Protocol):
    def get_ready_trial_ml_model_metadata(self, store_id: int) -> MLModelMetadata | None:
        ...

    def get_trial_store_timezone(self, store_id: int) -> str | None:
        ...

    def count_trial_zone_busy_tokens_at(
        self,
        store_id: int,
        trial_zone_id: int | None,
        at_time: datetime,
        exclude_token_id: int | None = None,
    ) -> int:
        ...

    def count_active_studios_for_zone(self, store_id: int, trial_zone_id: int | None) -> int:
        ...

    def list_recent_trial_zone_terminal_tokens(
        self,
        store_id: int,
        trial_zone_id: int | None,
        start_time: datetime,
        end_time: datetime,
    ) -> list[TrialQueueToken]:
        ...

    def has_active_trial_promotion_event(self, store_id: int, event_date) -> bool:
        ...

    def get_zone(self, zone_id: int):
        ...

    def get_studio(self, studio_id: int):
        ...


class TrialPredictionService:
    _artifact_cache: dict[tuple[int, str, str, float], object] = {}

    def __init__(self, repository: TrialPredictionRepository) -> None:
        self.repository = repository

    def predict_service_time(
        self,
        store_id: int,
        payload: TrialServiceTimePredictionRequest,
    ) -> ServiceTimePredictionResponse | None:
        metadata = self.repository.get_ready_trial_ml_model_metadata(store_id)
        if metadata is None or not metadata.artifact_path:
            return None

        artifact_path = Path(metadata.artifact_path)
        if not artifact_path.exists():
            return None
        cache_key = (
            store_id,
            metadata.model_version,
            str(artifact_path),
            artifact_path.stat().st_mtime,
        )

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

    def _build_features(self, store_id: int, payload: TrialServiceTimePredictionRequest) -> dict[str, int | float | str]:
        reference_time = self._normalize_to_utc(payload.requested_at or datetime.now(timezone.utc))
        timezone_name = self.repository.get_trial_store_timezone(store_id) or DEFAULT_TIMEZONE
        local_time = reference_time.astimezone(self._timezone_or_default(timezone_name))
        recent_tokens = self.repository.list_recent_trial_zone_terminal_tokens(
            store_id=store_id,
            trial_zone_id=payload.trial_zone_id,
            start_time=reference_time - timedelta(days=RECENT_HISTORY_DAYS),
            end_time=reference_time,
        )
        terminal_count = len(recent_tokens)
        cancelled_count = len(
            [
                token
                for token in recent_tokens
                if token.status in (TrialQueueTokenStatus.CANCELLED, TrialQueueTokenStatus.NO_SHOW)
            ]
        )
        recent_completed_durations = [
            (token.completed_at - token.service_started_at).total_seconds() / 60
            for token in recent_tokens
            if token.status == TrialQueueTokenStatus.COMPLETED
            and token.service_started_at is not None
            and token.completed_at is not None
            and token.completed_at > token.service_started_at
        ]
        zone = self.repository.get_zone(payload.trial_zone_id) if payload.trial_zone_id is not None else None
        studio = self.repository.get_studio(payload.assigned_studio_id) if payload.assigned_studio_id is not None else None

        return {
            "item_count": float(payload.item_count or 0),
            "trial_zone_busy_count_at_join": float(
                self.repository.count_trial_zone_busy_tokens_at(store_id, payload.trial_zone_id, reference_time)
            ),
            "trial_active_studio_count_at_join": float(
                self.repository.count_active_studios_for_zone(store_id, payload.trial_zone_id)
            ),
            "recent_cancellation_rate": (cancelled_count / terminal_count) if terminal_count else 0.0,
            "recent_average_service_minutes": (
                sum(recent_completed_durations) / len(recent_completed_durations) if recent_completed_durations else 0.0
            ),
            "hour_of_day": float(local_time.hour),
            "day_of_week": float(local_time.weekday()),
            "is_weekend": 1.0 if local_time.weekday() >= 5 else 0.0,
            "promotion_day_flag": 1.0 if self.repository.has_active_trial_promotion_event(store_id, local_time.date()) else 0.0,
            "customer_type": (payload.customer_type or "unknown").lower(),
            "trial_zone_id": str(payload.trial_zone_id or "none"),
            "assigned_studio_id": str(payload.assigned_studio_id or "none"),
            "trial_zone_type": zone.zone_type.value.lower() if zone is not None else "unknown",
            "trial_zone_gender": zone.gender.value.lower() if zone is not None else "unknown",
            "studio_type": studio.studio_type.value.lower() if studio is not None else "unknown",
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
