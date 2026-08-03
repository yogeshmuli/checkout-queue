from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.schemas.trial_analytics import TrialStoreAnalyticsResponse
from app.services.trial_analytics_service import TrialAnalyticsService

router = APIRouter(prefix="/trial/analytics", tags=["trial-analytics"])
trial_analytics_roles = (UserRole.SUPER_ADMIN, UserRole.STORE_ADMIN, UserRole.MANAGER)


@router.get("/stores/{store_id}", response_model=TrialStoreAnalyticsResponse)
def get_trial_store_analytics(
    store_id: int,
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*trial_analytics_roles)),
) -> TrialStoreAnalyticsResponse:
    return TrialAnalyticsService(db).get_store_analytics(store_id, days)
