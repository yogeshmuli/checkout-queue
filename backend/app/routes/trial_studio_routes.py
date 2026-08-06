from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.authorization import authorized_store_ids, ensure_store_access
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.schemas.trial_studio import TrialStudioCreateRequest, TrialStudioResponse, TrialStudioUpdateRequest
from app.services.trial_studio_service import TrialStudioService

router = APIRouter(tags=["trial-studios"])

trial_admin_roles = (UserRole.SUPER_ADMIN, UserRole.STORE_ADMIN, UserRole.MANAGER)


@router.post("/trial/studios", response_model=TrialStudioResponse, status_code=201)
def create_trial_studio(payload: TrialStudioCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialStudioResponse:
    zone = TrialStudioService(db).get_zone(payload.trial_zone_id)
    ensure_store_access(db, current_user, zone.store_id)
    return TrialStudioService(db).create_studio(payload)


@router.get("/trial/studios", response_model=list[TrialStudioResponse])
def list_trial_studios(include_inactive: bool = Query(default=False), store_id: int | None = Query(default=None), trial_zone_id: int | None = Query(default=None), db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> list[TrialStudioResponse]:
    service = TrialStudioService(db)
    if store_id is not None:
        ensure_store_access(db, current_user, store_id)
    if trial_zone_id is not None:
        ensure_store_access(db, current_user, service.get_zone(trial_zone_id).store_id)
    return service.list_studios(include_inactive=include_inactive, store_id=store_id, trial_zone_id=trial_zone_id, store_ids=authorized_store_ids(db, current_user))


@router.patch("/trial/studios/{studio_id}", response_model=TrialStudioResponse)
def update_trial_studio(studio_id: int, payload: TrialStudioUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialStudioResponse:
    service = TrialStudioService(db)
    studio = service.get_studio(studio_id)
    ensure_store_access(db, current_user, service.get_zone(studio.trial_zone_id).store_id)
    if payload.trial_zone_id is not None:
        ensure_store_access(db, current_user, service.get_zone(payload.trial_zone_id).store_id)
    return service.update_studio(studio_id, payload)


@router.delete("/trial/studios/{studio_id}", response_model=TrialStudioResponse)
def delete_trial_studio(studio_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialStudioResponse:
    service = TrialStudioService(db)
    studio = service.get_studio(studio_id)
    ensure_store_access(db, current_user, service.get_zone(studio.trial_zone_id).store_id)
    return service.deactivate_studio(studio_id)
