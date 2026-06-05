from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.schemas.trial_zone import TrialZoneCreateRequest, TrialZoneResponse, TrialZoneUpdateRequest
from app.services.trial_zone_service import TrialZoneService

router = APIRouter(tags=["trial-zones"])

trial_admin_roles = (UserRole.SUPER_ADMIN, UserRole.STORE_ADMIN, UserRole.MANAGER)


@router.post("/trial/zones", response_model=TrialZoneResponse, status_code=201)
def create_trial_zone(payload: TrialZoneCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialZoneResponse:
    return TrialZoneService(db).create_zone(payload)


@router.get("/trial/zones", response_model=list[TrialZoneResponse])
def list_trial_zones(include_inactive: bool = Query(default=False), store_id: int | None = Query(default=None), db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> list[TrialZoneResponse]:
    return TrialZoneService(db).list_zones(include_inactive=include_inactive, store_id=store_id)


@router.patch("/trial/zones/{zone_id}", response_model=TrialZoneResponse)
def update_trial_zone(zone_id: int, payload: TrialZoneUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialZoneResponse:
    return TrialZoneService(db).update_zone(zone_id, payload)


@router.delete("/trial/zones/{zone_id}", response_model=TrialZoneResponse)
def delete_trial_zone(zone_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialZoneResponse:
    return TrialZoneService(db).deactivate_zone(zone_id)
