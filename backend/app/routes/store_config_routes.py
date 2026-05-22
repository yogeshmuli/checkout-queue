from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.schemas.store_config import StoreConfigResponse, StoreConfigUpdateRequest
from app.services.store_config_service import StoreConfigService

router = APIRouter(prefix="/stores/{store_id}/config", tags=["store-config"])

store_config_admin_roles = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_ADMIN,
    UserRole.MANAGER,
)


@router.get("", response_model=StoreConfigResponse)
def get_store_config(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*store_config_admin_roles)),
) -> StoreConfigResponse:
    return StoreConfigService(db).get_store_config(store_id)


@router.put("", response_model=StoreConfigResponse)
def upsert_store_config(
    store_id: int,
    payload: StoreConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*store_config_admin_roles)),
) -> StoreConfigResponse:
    return StoreConfigService(db).upsert_store_config(store_id, payload)
