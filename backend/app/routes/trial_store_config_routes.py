from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.schemas.trial_store_config import TrialStoreConfigResponse, TrialStoreConfigUpdateRequest
from app.services.trial_store_config_service import TrialStoreConfigService

router = APIRouter(tags=["trial-config"])

trial_admin_roles = (UserRole.SUPER_ADMIN, UserRole.STORE_ADMIN, UserRole.MANAGER)


@router.get("/stores/{store_id}/trial-config", response_model=TrialStoreConfigResponse)
def get_trial_config(store_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialStoreConfigResponse:
    return TrialStoreConfigService(db).get_config(store_id)


@router.put("/stores/{store_id}/trial-config", response_model=TrialStoreConfigResponse)
def update_trial_config(store_id: int, payload: TrialStoreConfigUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialStoreConfigResponse:
    return TrialStoreConfigService(db).update_config(store_id, payload)
