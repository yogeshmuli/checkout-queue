from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.schemas.calendar import StoreCalendarResponse, StoreCalendarUpdateRequest
from app.services.calendar_service import CalendarService

router = APIRouter(prefix="/stores/{store_id}/calendar", tags=["store-calendar"])

calendar_admin_roles = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_ADMIN,
    UserRole.MANAGER,
)


@router.get("", response_model=StoreCalendarResponse)
def get_store_calendar(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*calendar_admin_roles)),
) -> StoreCalendarResponse:
    return CalendarService(db).get_calendar(store_id)


@router.put("", response_model=StoreCalendarResponse)
def update_store_calendar(
    store_id: int,
    payload: StoreCalendarUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*calendar_admin_roles)),
) -> StoreCalendarResponse:
    return CalendarService(db).update_calendar(store_id, payload)
