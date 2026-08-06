from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.authorization import require_store_roles
from app.models.user import User, UserRole
from app.schemas.trial_calendar import TrialCalendarResponse, TrialCalendarUpdateRequest
from app.services.trial_calendar_service import TrialCalendarService

router = APIRouter(tags=["trial-calendar"])

trial_admin_roles = (UserRole.SUPER_ADMIN, UserRole.STORE_ADMIN, UserRole.MANAGER)


@router.get("/stores/{store_id}/trial-calendar", response_model=TrialCalendarResponse)
def get_trial_calendar(store_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_store_roles(*trial_admin_roles))) -> TrialCalendarResponse:
    return TrialCalendarService(db).get_calendar(store_id)


@router.put("/stores/{store_id}/trial-calendar", response_model=TrialCalendarResponse)
def update_trial_calendar(store_id: int, payload: TrialCalendarUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_store_roles(*trial_admin_roles))) -> TrialCalendarResponse:
    return TrialCalendarService(db).update_calendar(store_id, payload)
