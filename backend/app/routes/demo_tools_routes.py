from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.schemas.demo_tools import DemoTrainingDataResponse
from app.services.demo_tools_service import DemoToolsService

router = APIRouter(prefix="/demotools", tags=["demo-tools"])


@router.post("/ml-training-data", response_model=DemoTrainingDataResponse, status_code=201)
def seed_ml_training_data(
    replace: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
) -> DemoTrainingDataResponse:
    return DemoToolsService(db).seed_ml_training_data(replace=replace)


@router.get("/ml-training-data/status", response_model=DemoTrainingDataResponse)
def get_ml_training_data_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
) -> DemoTrainingDataResponse:
    return DemoToolsService(db).get_ml_training_data_status()


@router.delete("/ml-training-data", response_model=DemoTrainingDataResponse)
def clean_ml_training_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
) -> DemoTrainingDataResponse:
    return DemoToolsService(db).clean_ml_training_data()
