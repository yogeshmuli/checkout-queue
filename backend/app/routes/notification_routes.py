from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.schemas.notification import NotificationLogResponse, StoreNotificationConfigResponse, StoreNotificationConfigUpdateRequest
from app.services.notification_service import NotificationService


router = APIRouter(prefix="/stores/{store_id}", tags=["notifications"])

notification_admin_roles = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_ADMIN,
    UserRole.MANAGER,
)


@router.get("/notification-config", response_model=StoreNotificationConfigResponse)
def get_notification_config(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*notification_admin_roles)),
) -> StoreNotificationConfigResponse:
    return NotificationService(db).get_config(store_id)


@router.put("/notification-config", response_model=StoreNotificationConfigResponse)
def update_notification_config(
    store_id: int,
    payload: StoreNotificationConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*notification_admin_roles)),
) -> StoreNotificationConfigResponse:
    return NotificationService(db).update_config(store_id, payload)


@router.get("/notification-logs", response_model=list[NotificationLogResponse])
def list_notification_logs(
    store_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*notification_admin_roles)),
) -> list[NotificationLogResponse]:
    return NotificationService(db).list_logs(store_id, limit)
