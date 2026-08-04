import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import joblib
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ml_model_metadata import MLModelMetadata
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.repositories.ml_repository import MLRepository
from app.schemas.ml import MLModelMetadataResponse
from app.services.ml_model_fitting import fit_service_time_model


DEFAULT_TIMEZONE = "Asia/Kolkata"
RECENT_HISTORY_DAYS = 7


class MLTrainingService:
    MODEL_TYPE = "random_forest_service_time_v2"

    def __init__(self, db: Session) -> None:
        self.repository = MLRepository(db)

    def train_store_model(self, store_id: int) -> MLModelMetadataResponse:
        store = self.repository.get_store_by_id(store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

        rows = self._training_rows(store_id)
        if len(rows) < settings.ML_MIN_TRAINING_SAMPLES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"At least {settings.ML_MIN_TRAINING_SAMPLES} completed checkout records are required for ML training",
            )

        return self._train_rows(store_id, rows)

    def train_uploaded_rows(self, store_id: int, rows: list[dict[str, object]], filename: str, content: bytes, uploaded_by_user_id: int) -> MLModelMetadataResponse:
        if self.repository.get_store_by_id(store_id) is None:
            raise HTTPException(status_code=404, detail="Store not found")
        return self._train_rows(store_id, rows, filename, content, uploaded_by_user_id)

    def _train_rows(self, store_id, rows, filename=None, content=None, uploaded_by_user_id=None):
        fitted = fit_service_time_model(rows)

        trained_at = datetime.now(timezone.utc)
        model_version = trained_at.strftime("service-time-%Y%m%d%H%M%S%f")
        artifact_path = self._write_artifact(
            store_id=store_id,
            model_version=model_version,
            artifact={
                "model_type": self.MODEL_TYPE,
                "model_version": model_version,
                "trained_at": trained_at.isoformat(),
                "sample_size": len(rows),
                "recent_history_days": RECENT_HISTORY_DAYS,
                "model": fitted.model,
            },
        )
        source_file_path = None
        if content is not None:
            source_file_path = artifact_path.with_name(f"{model_version}-source.xlsx")
            source_file_path.write_bytes(content)

        metadata = MLModelMetadata(
            store_id=store_id,
            model_type=self.MODEL_TYPE,
            model_version=model_version,
            status="READY",
            artifact_path=str(artifact_path),
            sample_size=len(rows),
            trained_at=trained_at,
            mae=fitted.mae,
            r2_score=fitted.r2_score,
            accuracy_score=fitted.accuracy_score,
            data_quality_score=1.0,
            feature_importance=json.dumps(fitted.feature_importance),
            training_source="EXCEL_UPLOAD" if content is not None else "DATABASE",
            original_filename=Path(filename).name[:255] if filename else None,
            source_file_path=str(source_file_path) if source_file_path else None,
            uploaded_by_user_id=uploaded_by_user_id,
            validation_summary=json.dumps({"valid_rows": len(rows), "invalid_rows": 0}) if content is not None else None,
        )
        self.repository.create_metadata(metadata)
        self.repository.commit()
        self.repository.refresh(metadata)
        return self._to_response(metadata)

    def get_store_metadata(self, store_id: int) -> MLModelMetadataResponse:
        store = self.repository.get_store_by_id(store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

        metadata = self.repository.get_latest_metadata(store_id, self.MODEL_TYPE)
        if metadata is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ML model metadata not found")
        return self._to_response(metadata)

    def _training_rows(self, store_id: int) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        timezone_name = self.repository.get_store_timezone(store_id) or DEFAULT_TIMEZONE
        store_tz = self._timezone_or_default(timezone_name)

        for token in self.repository.list_completed_training_tokens(store_id):
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

    def _build_features(
        self,
        token: QueueToken,
        reference_time: datetime,
        store_tz: ZoneInfo,
    ) -> dict[str, int | float | str]:
        local_time = reference_time.astimezone(store_tz)
        recent_tokens = self.repository.list_recent_section_terminal_tokens(
            store_id=token.store_id,
            section_id=token.section_id,
            start_time=reference_time - timedelta(days=RECENT_HISTORY_DAYS),
            end_time=reference_time,
        )
        terminal_count = len(recent_tokens)
        cancelled_count = len(
            [
                recent_token
                for recent_token in recent_tokens
                if recent_token.status in (QueueTokenStatus.CANCELLED, QueueTokenStatus.NO_SHOW)
            ]
        )
        recent_completed_durations = [
            (recent_token.completed_at - recent_token.service_started_at).total_seconds() / 60
            for recent_token in recent_tokens
            if recent_token.status == QueueTokenStatus.COMPLETED
            and recent_token.service_started_at is not None
            and recent_token.completed_at is not None
            and recent_token.completed_at > recent_token.service_started_at
        ]

        return {
            "item_count": float(token.item_count or 0),
            "section_busy_count_at_join": float(
                self.repository.count_section_busy_tokens_at(
                    token.store_id,
                    token.section_id,
                    reference_time,
                    token.id,
                )
            ),
            "section_active_counter_count_at_join": float(
                self.repository.count_active_counters_for_section(token.store_id, token.section_id)
            ),
            "recent_cancellation_rate": (cancelled_count / terminal_count) if terminal_count else 0.0,
            "recent_average_service_minutes": (
                sum(recent_completed_durations) / len(recent_completed_durations) if recent_completed_durations else 0.0
            ),
            "hour_of_day": float(local_time.hour),
            "day_of_week": float(local_time.weekday()),
            "is_weekend": 1.0 if local_time.weekday() >= 5 else 0.0,
            "promotion_day_flag": 1.0
            if self.repository.has_active_promotion_event(token.store_id, local_time.date())
            else 0.0,
            "basket_size": (token.basket_size or "unknown").lower(),
            "cart_type": (token.cart_type or "unknown").lower(),
            "customer_type": (token.customer_type or "unknown").lower(),
            "section_id": str(token.section_id or "none"),
            "assigned_counter_id": str(token.assigned_counter_id or "none"),
        }

    def _write_artifact(self, store_id: int, model_version: str, artifact: dict[str, object]) -> Path:
        model_dir = Path(settings.ML_MODEL_DIR) / f"store_{store_id}"
        model_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = model_dir / f"{model_version}.joblib"
        joblib.dump(artifact, artifact_path)
        return artifact_path

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
            training_source=metadata.training_source,
            original_filename=metadata.original_filename,
            source_file_path=metadata.source_file_path,
            uploaded_by_user_id=metadata.uploaded_by_user_id,
            validation_summary=json.loads(metadata.validation_summary) if metadata.validation_summary else None,
        )
