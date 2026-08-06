from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.authorization import require_store_roles
from app.models.user import User, UserRole
from app.repositories.queue_repository import QueueRepository
from app.repositories.trial_queue_repository import TrialQueueRepository
from app.schemas.ml import MLModelMetadataResponse, ServiceTimePredictionRequest, ServiceTimePredictionResponse, TrialServiceTimePredictionRequest
from app.services.ml_training_service import MLTrainingService
from app.services.ml_excel_service import MLExcelService
from app.services.prediction_service import PredictionService
from app.services.trial_ml_training_service import TrialMLTrainingService
from app.services.trial_prediction_service import TrialPredictionService

router = APIRouter(prefix="/ml", tags=["machine-learning"])

ml_admin_roles = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_ADMIN,
    UserRole.MANAGER,
)


async def _read_training_upload(file: UploadFile) -> tuple[str, bytes]:
    filename = file.filename or ""
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=422, detail="Only .xlsx training workbooks are accepted")
    content = await file.read(settings.ML_TRAINING_UPLOAD_MAX_BYTES + 1)
    if len(content) > settings.ML_TRAINING_UPLOAD_MAX_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Training workbook exceeds the configured upload limit")
    return filename, content


@router.post("/stores/{store_id}/train", response_model=MLModelMetadataResponse)
def train_store_model(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_roles(*ml_admin_roles)),
) -> MLModelMetadataResponse:
    return MLTrainingService(db).train_store_model(store_id)


@router.get("/stores/{store_id}/training-template")
def download_store_training_template(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_roles(*ml_admin_roles)),
):
    service = MLTrainingService(db)
    content = MLExcelService(service.repository, "checkout").build_template(store_id)
    return StreamingResponse(BytesIO(content), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="checkout-store-{store_id}-ml-training.xlsx"'})


@router.post("/stores/{store_id}/train-upload", response_model=MLModelMetadataResponse)
async def train_store_model_from_upload(
    store_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_roles(*ml_admin_roles)),
) -> MLModelMetadataResponse:
    filename, content = await _read_training_upload(file)
    service = MLTrainingService(db)
    rows = MLExcelService(service.repository, "checkout").parse(store_id, content)
    return service.train_uploaded_rows(store_id, rows, filename, content, current_user.id)


@router.get("/stores/{store_id}/metadata", response_model=MLModelMetadataResponse)
def get_store_model_metadata(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_roles(*ml_admin_roles)),
) -> MLModelMetadataResponse:
    return MLTrainingService(db).get_store_metadata(store_id)


@router.post("/stores/{store_id}/predict-service-time", response_model=ServiceTimePredictionResponse)
def predict_store_service_time(
    store_id: int,
    payload: ServiceTimePredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_roles(*ml_admin_roles)),
) -> ServiceTimePredictionResponse:
    prediction = PredictionService(QueueRepository(db)).predict_service_time(store_id, payload)
    if prediction is None:
        return ServiceTimePredictionResponse(service_time_minutes=0, calculation_method="ML_UNAVAILABLE")
    return prediction


@router.post("/trial/stores/{store_id}/train", response_model=MLModelMetadataResponse)
def train_trial_store_model(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_roles(*ml_admin_roles)),
) -> MLModelMetadataResponse:
    return TrialMLTrainingService(db).train_store_model(store_id)


@router.get("/trial/stores/{store_id}/training-template")
def download_trial_store_training_template(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_roles(*ml_admin_roles)),
):
    service = TrialMLTrainingService(db)
    content = MLExcelService(service.repository, "trial").build_template(store_id)
    return StreamingResponse(BytesIO(content), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="trial-store-{store_id}-ml-training.xlsx"'})


@router.post("/trial/stores/{store_id}/train-upload", response_model=MLModelMetadataResponse)
async def train_trial_store_model_from_upload(
    store_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_roles(*ml_admin_roles)),
) -> MLModelMetadataResponse:
    filename, content = await _read_training_upload(file)
    service = TrialMLTrainingService(db)
    rows = MLExcelService(service.repository, "trial").parse(store_id, content)
    return service.train_uploaded_rows(store_id, rows, filename, content, current_user.id)


@router.get("/trial/stores/{store_id}/metadata", response_model=MLModelMetadataResponse)
def get_trial_store_model_metadata(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_roles(*ml_admin_roles)),
) -> MLModelMetadataResponse:
    return TrialMLTrainingService(db).get_store_metadata(store_id)


@router.post("/trial/stores/{store_id}/predict-service-time", response_model=ServiceTimePredictionResponse)
def predict_trial_store_service_time(
    store_id: int,
    payload: TrialServiceTimePredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_roles(*ml_admin_roles)),
) -> ServiceTimePredictionResponse:
    prediction = TrialPredictionService(TrialQueueRepository(db)).predict_service_time(store_id, payload)
    if prediction is None:
        return ServiceTimePredictionResponse(service_time_minutes=0, calculation_method="ML_UNAVAILABLE")
    return prediction
