from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.authorization import authorized_store_ids, ensure_store_access
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.schemas.store import StoreCreateRequest, StoreResponse, StoreUpdateRequest
from app.services.store_service import StoreService

router = APIRouter(prefix="/stores", tags=["stores"])

store_admin_roles = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_ADMIN,
    UserRole.MANAGER,
)


@router.post("", response_model=StoreResponse, status_code=201)
def create_store(
    payload: StoreCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
) -> StoreResponse:
    return StoreService(db).create_store(payload)


@router.get("", response_model=list[StoreResponse])
def list_stores(
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*store_admin_roles)),
) -> list[StoreResponse]:
    return StoreService(db).list_stores(
        include_inactive=include_inactive,
        store_ids=authorized_store_ids(db, current_user),
    )


@router.get("/{store_id}", response_model=StoreResponse)
def get_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*store_admin_roles)),
) -> StoreResponse:
    ensure_store_access(db, current_user, store_id)
    return StoreService(db).get_store(store_id)


@router.patch("/{store_id}", response_model=StoreResponse)
def update_store(
    store_id: int,
    payload: StoreUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*store_admin_roles)),
) -> StoreResponse:
    ensure_store_access(db, current_user, store_id)
    return StoreService(db).update_store(store_id, payload)


@router.delete("/{store_id}", response_model=StoreResponse)
def delete_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
) -> StoreResponse:
    return StoreService(db).deactivate_store(store_id)
