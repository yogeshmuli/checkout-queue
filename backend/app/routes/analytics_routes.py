from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.authorization import require_store_roles
from app.models.user import User, UserRole
from app.schemas.analytics import StoreAnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

analytics_admin_roles = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_ADMIN,
    UserRole.MANAGER,
)


@router.get("/stores/{store_id}", response_model=StoreAnalyticsResponse)
def get_store_analytics(
    store_id: int,
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_roles(*analytics_admin_roles)),
) -> StoreAnalyticsResponse:
    return AnalyticsService(db).get_store_analytics(store_id, days)
