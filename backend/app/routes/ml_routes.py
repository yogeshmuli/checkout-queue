from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.repositories.queue_repository import QueueRepository
from app.repositories.trial_repository import TrialRepository
from app.schemas.ml import MLModelMetadataResponse, ServiceTimePredictionRequest, ServiceTimePredictionResponse, TrialServiceTimePredictionRequest
from app.services.ml_training_service import MLTrainingService
from app.services.prediction_service import PredictionService
from app.services.trial_ml_training_service import TrialMLTrainingService
from app.services.trial_prediction_service import TrialPredictionService

router = APIRouter(prefix="/ml", tags=["machine-learning"])

ml_admin_roles = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_ADMIN,
    UserRole.MANAGER,
)


@router.post("/stores/{store_id}/train", response_model=MLModelMetadataResponse)
def train_store_model(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ml_admin_roles)),
) -> MLModelMetadataResponse:
    return MLTrainingService(db).train_store_model(store_id)


@router.get("/stores/{store_id}/metadata", response_model=MLModelMetadataResponse)
def get_store_model_metadata(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ml_admin_roles)),
) -> MLModelMetadataResponse:
    return MLTrainingService(db).get_store_metadata(store_id)


@router.post("/stores/{store_id}/predict-service-time", response_model=ServiceTimePredictionResponse)
def predict_store_service_time(
    store_id: int,
    payload: ServiceTimePredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ml_admin_roles)),
) -> ServiceTimePredictionResponse:
    prediction = PredictionService(QueueRepository(db)).predict_service_time(store_id, payload)
    if prediction is None:
        return ServiceTimePredictionResponse(service_time_minutes=0, calculation_method="ML_UNAVAILABLE")
    return prediction


@router.post("/trial/stores/{store_id}/train", response_model=MLModelMetadataResponse)
def train_trial_store_model(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ml_admin_roles)),
) -> MLModelMetadataResponse:
    return TrialMLTrainingService(db).train_store_model(store_id)


@router.get("/trial/stores/{store_id}/metadata", response_model=MLModelMetadataResponse)
def get_trial_store_model_metadata(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ml_admin_roles)),
) -> MLModelMetadataResponse:
    return TrialMLTrainingService(db).get_store_metadata(store_id)


@router.post("/trial/stores/{store_id}/predict-service-time", response_model=ServiceTimePredictionResponse)
def predict_trial_store_service_time(
    store_id: int,
    payload: TrialServiceTimePredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ml_admin_roles)),
) -> ServiceTimePredictionResponse:
    prediction = TrialPredictionService(TrialRepository(db)).predict_service_time(store_id, payload)
    if prediction is None:
        return ServiceTimePredictionResponse(service_time_minutes=0, calculation_method="ML_UNAVAILABLE")
    return prediction
