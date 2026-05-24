import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import joblib
from fastapi import HTTPException, status
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ml_model_metadata import MLModelMetadata
from app.models.trial import TrialQueueToken, TrialQueueTokenStatus
from app.repositories.trial_repository import TrialRepository
from app.schemas.ml import MLModelMetadataResponse


DEFAULT_TIMEZONE = "Asia/Kolkata"
RECENT_HISTORY_DAYS = 7


class TrialMLTrainingService:
    MODEL_TYPE = "random_forest_trial_service_time_v1"

    def __init__(self, db: Session) -> None:
        self.repository = TrialRepository(db)

    def train_store_model(self, store_id: int) -> MLModelMetadataResponse:
        store = self.repository.get_store(store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

        rows = self._training_rows(store_id)
        if len(rows) < settings.ML_MIN_TRAINING_SAMPLES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"At least {settings.ML_MIN_TRAINING_SAMPLES} completed trial records are required for ML training",
            )

        features = [row["features"] for row in rows]
        actuals = [row["duration_minutes"] for row in rows]
        model = Pipeline(
            steps=[
                ("features", DictVectorizer(sparse=False)),
                (
                    "regressor",
                    RandomForestRegressor(
                        n_estimators=100,
                        random_state=42,
                        min_samples_leaf=1,
                    ),
                ),
            ]
        )
        model.fit(features, actuals)
        predictions = [float(prediction) for prediction in model.predict(features)]

        mae = float(mean_absolute_error(actuals, predictions))
        r2 = float(r2_score(actuals, predictions)) if len(set(actuals)) > 1 else 0.0
        mean_actual = sum(actuals) / len(actuals)
        accuracy_score = max(0.0, min(1.0, 1 - (mae / mean_actual))) if mean_actual else 0.0
        feature_importance = self._feature_importance(model)

        trained_at = datetime.now(timezone.utc)
        model_version = trained_at.strftime("trial-service-time-%Y%m%d%H%M%S")
        artifact_path = self._write_artifact(
            store_id=store_id,
            model_version=model_version,
            artifact={
                "model_type": self.MODEL_TYPE,
                "model_version": model_version,
                "trained_at": trained_at.isoformat(),
                "sample_size": len(rows),
                "recent_history_days": RECENT_HISTORY_DAYS,
                "model": model,
            },
        )

        metadata = MLModelMetadata(
            store_id=store_id,
            model_type=self.MODEL_TYPE,
            model_version=model_version,
            status="READY",
            artifact_path=str(artifact_path),
            sample_size=len(rows),
            trained_at=trained_at,
            mae=mae,
            r2_score=r2,
            accuracy_score=accuracy_score,
            data_quality_score=1.0,
            feature_importance=json.dumps(feature_importance),
        )
        self.repository.create(metadata)
        self.repository.commit()
        self.repository.refresh(metadata)
        return self._to_response(metadata)

    def get_store_metadata(self, store_id: int) -> MLModelMetadataResponse:
        store = self.repository.get_store(store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

        metadata = self.repository.get_ready_trial_ml_model_metadata(store_id)
        if metadata is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial ML model metadata not found")
        return self._to_response(metadata)

    def _training_rows(self, store_id: int) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        timezone_name = self.repository.get_trial_store_timezone(store_id) or DEFAULT_TIMEZONE
        store_tz = self._timezone_or_default(timezone_name)

        for token in self.repository.list_completed_trial_training_tokens(store_id):
            if token.service_started_at is None or token.completed_at is None:
                continue
            duration_minutes = (token.completed_at - token.service_started_at).total_seconds() / 60
            if duration_minutes <= 0:
                continue
            created_at = self._normalize_to_utc(token.created_at or token.service_started_at)
            rows.append(
                {
                    "features": self._build_features(token, created_at, store_tz),
                    "duration_minutes": max(1.0, min(240.0, duration_minutes)),
                }
            )
        return rows

    def _build_features(self, token: TrialQueueToken, reference_time: datetime, store_tz: ZoneInfo) -> dict[str, int | float | str]:
        local_time = reference_time.astimezone(store_tz)
        recent_tokens = self.repository.list_recent_trial_zone_terminal_tokens(
            store_id=token.store_id,
            trial_zone_id=token.trial_zone_id,
            start_time=reference_time - timedelta(days=RECENT_HISTORY_DAYS),
            end_time=reference_time,
        )
        terminal_count = len(recent_tokens)
        cancelled_count = len(
            [
                recent_token
                for recent_token in recent_tokens
                if recent_token.status in (TrialQueueTokenStatus.CANCELLED, TrialQueueTokenStatus.NO_SHOW)
            ]
        )
        recent_completed_durations = [
            (recent_token.completed_at - recent_token.service_started_at).total_seconds() / 60
            for recent_token in recent_tokens
            if recent_token.status == TrialQueueTokenStatus.COMPLETED
            and recent_token.service_started_at is not None
            and recent_token.completed_at is not None
            and recent_token.completed_at > recent_token.service_started_at
        ]
        zone = self.repository.get_zone(token.trial_zone_id) if token.trial_zone_id is not None else None
        studio = self.repository.get_studio(token.assigned_studio_id) if token.assigned_studio_id is not None else None

        return {
            "item_count": float(token.item_count or 0),
            "trial_zone_busy_count_at_join": float(
                self.repository.count_trial_zone_busy_tokens_at(
                    token.store_id,
                    token.trial_zone_id,
                    reference_time,
                    token.id,
                )
            ),
            "trial_active_studio_count_at_join": float(
                self.repository.count_active_studios_for_zone(token.store_id, token.trial_zone_id)
            ),
            "recent_cancellation_rate": (cancelled_count / terminal_count) if terminal_count else 0.0,
            "recent_average_service_minutes": (
                sum(recent_completed_durations) / len(recent_completed_durations) if recent_completed_durations else 0.0
            ),
            "hour_of_day": float(local_time.hour),
            "day_of_week": float(local_time.weekday()),
            "is_weekend": 1.0 if local_time.weekday() >= 5 else 0.0,
            "promotion_day_flag": 1.0
            if self.repository.has_active_trial_promotion_event(token.store_id, local_time.date())
            else 0.0,
            "customer_type": (token.customer_type or "unknown").lower(),
            "trial_zone_id": str(token.trial_zone_id or "none"),
            "assigned_studio_id": str(token.assigned_studio_id or "none"),
            "trial_zone_type": zone.zone_type.value.lower() if zone is not None else "unknown",
            "trial_zone_gender": zone.gender.value.lower() if zone is not None else "unknown",
            "studio_type": studio.studio_type.value.lower() if studio is not None else "unknown",
        }

    def _write_artifact(self, store_id: int, model_version: str, artifact: dict[str, object]) -> Path:
        model_dir = Path(settings.ML_MODEL_DIR) / f"trial_store_{store_id}"
        model_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = model_dir / f"{model_version}.joblib"
        joblib.dump(artifact, artifact_path)
        return artifact_path

    def _feature_importance(self, model: Pipeline) -> dict[str, float]:
        vectorizer = model.named_steps["features"]
        regressor = model.named_steps["regressor"]
        feature_names = vectorizer.get_feature_names_out()
        importances = regressor.feature_importances_
        grouped: dict[str, float] = {}
        for feature_name, importance in zip(feature_names, importances):
            base_name = feature_name.split("=", 1)[0]
            grouped[base_name] = grouped.get(base_name, 0.0) + float(importance)
        return dict(sorted(grouped.items()))

    def _normalize_to_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _timezone_or_default(self, timezone_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            return ZoneInfo(DEFAULT_TIMEZONE)

    def _to_response(self, metadata: MLModelMetadata) -> MLModelMetadataResponse:
        feature_importance = None
        if metadata.feature_importance:
            try:
                feature_importance = json.loads(metadata.feature_importance)
            except json.JSONDecodeError:
                feature_importance = None

        return MLModelMetadataResponse(
            id=metadata.id,
            store_id=metadata.store_id,
            model_type=metadata.model_type,
            model_version=metadata.model_version,
            status=metadata.status,
            sample_size=metadata.sample_size,
            trained_at=metadata.trained_at,
            mae=metadata.mae,
            r2_score=metadata.r2_score,
            accuracy_score=metadata.accuracy_score,
            data_quality_score=metadata.data_quality_score,
            feature_importance=feature_importance,
            error_message=metadata.error_message,
        )
