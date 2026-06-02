from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.trial import TrialQueueTokenStatus
from app.models.user import User, UserRole
from app.schemas.trial import (
    TrialCalendarResponse,
    TrialCalendarUpdateRequest,
    TrialQueueEventRequest,
    TrialQueueEventResponse,
    TrialQueueJoinRequest,
    TrialQueueJoinResponse,
    TrialQueueTokenResponse,
    TrialStoreConfigResponse,
    TrialStoreConfigUpdateRequest,
    TrialStoreResponse,
    TrialStudioCreateRequest,
    TrialStudioQueueResponse,
    TrialStudioResponse,
    TrialStudioStatusUpdateRequest,
    TrialStudioUpdateRequest,
    TrialZoneStudioQueuesResponse,
    TrialTokenCancelRequest,
    TrialZoneCreateRequest,
    TrialZoneResponse,
    TrialZoneUpdateRequest,
)
from app.services.trial_service import TrialService

router = APIRouter(tags=["trial-queue"])

trial_admin_roles = (UserRole.SUPER_ADMIN, UserRole.STORE_ADMIN, UserRole.MANAGER)
trial_staff_roles = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_ADMIN,
    UserRole.MANAGER,
    UserRole.TRIAL_ZONE_ASSISTANT,
)


@router.post("/trial/zones", response_model=TrialZoneResponse, status_code=201)
def create_trial_zone(payload: TrialZoneCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialZoneResponse:
    return TrialService(db).create_zone(payload)


@router.get("/trial/zones", response_model=list[TrialZoneResponse])
def list_trial_zones(include_inactive: bool = Query(default=False), store_id: int | None = Query(default=None), db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> list[TrialZoneResponse]:
    return TrialService(db).list_zones(include_inactive=include_inactive, store_id=store_id)


@router.patch("/trial/zones/{zone_id}", response_model=TrialZoneResponse)
def update_trial_zone(zone_id: int, payload: TrialZoneUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialZoneResponse:
    return TrialService(db).update_zone(zone_id, payload)


@router.delete("/trial/zones/{zone_id}", response_model=TrialZoneResponse)
def delete_trial_zone(zone_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialZoneResponse:
    return TrialService(db).deactivate_zone(zone_id)


@router.post("/trial/studios", response_model=TrialStudioResponse, status_code=201)
def create_trial_studio(payload: TrialStudioCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialStudioResponse:
    return TrialService(db).create_studio(payload)


@router.get("/trial/studios", response_model=list[TrialStudioResponse])
def list_trial_studios(include_inactive: bool = Query(default=False), store_id: int | None = Query(default=None), trial_zone_id: int | None = Query(default=None), db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> list[TrialStudioResponse]:
    return TrialService(db).list_studios(include_inactive=include_inactive, store_id=store_id, trial_zone_id=trial_zone_id)


@router.patch("/trial/studios/{studio_id}", response_model=TrialStudioResponse)
def update_trial_studio(studio_id: int, payload: TrialStudioUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialStudioResponse:
    return TrialService(db).update_studio(studio_id, payload)


@router.delete("/trial/studios/{studio_id}", response_model=TrialStudioResponse)
def delete_trial_studio(studio_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialStudioResponse:
    return TrialService(db).deactivate_studio(studio_id)


@router.get("/stores/{store_id}/trial-config", response_model=TrialStoreConfigResponse)
def get_trial_config(store_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialStoreConfigResponse:
    return TrialService(db).get_config(store_id)


@router.put("/stores/{store_id}/trial-config", response_model=TrialStoreConfigResponse)
def update_trial_config(store_id: int, payload: TrialStoreConfigUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialStoreConfigResponse:
    return TrialService(db).update_config(store_id, payload)


@router.get("/stores/{store_id}/trial-calendar", response_model=TrialCalendarResponse)
def get_trial_calendar(store_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialCalendarResponse:
    return TrialService(db).get_calendar(store_id)


@router.put("/stores/{store_id}/trial-calendar", response_model=TrialCalendarResponse)
def update_trial_calendar(store_id: int, payload: TrialCalendarUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_admin_roles))) -> TrialCalendarResponse:
    return TrialService(db).update_calendar(store_id, payload)


@router.get("/trial/queue/store-zones", response_model=list[TrialStoreResponse])
def list_trial_store_zones(db: Session = Depends(get_db)) -> list[TrialStoreResponse]:
    return TrialService(db).list_store_zones()


@router.post("/trial/queue/join", response_model=TrialQueueJoinResponse)
def join_trial_queue(payload: TrialQueueJoinRequest, db: Session = Depends(get_db)) -> TrialQueueJoinResponse:
    return TrialService(db).join_queue(payload)


@router.get("/trial/queue/status", response_model=TrialQueueTokenResponse)
def get_trial_token_status(token_id: int | None = None, store_id: int | None = None, phone_number: str | None = None, db: Session = Depends(get_db)) -> TrialQueueTokenResponse:
    return TrialService(db).get_token_status(token_id=token_id, store_id=store_id, phone_number=phone_number)


@router.get("/trial/queue/tokens", response_model=list[TrialQueueTokenResponse])
def list_trial_queue_tokens(store_id: int | None = None, trial_zone_id: int | None = None, studio_id: int | None = None, status: TrialQueueTokenStatus | None = None, include_terminal: bool = Query(default=False), db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> list[TrialQueueTokenResponse]:
    return TrialService(db).list_queue_tokens(store_id=store_id, trial_zone_id=trial_zone_id, studio_id=studio_id, token_status=status, include_terminal=include_terminal, current_user=current_user)


@router.post("/trial/queue/events", response_model=TrialQueueEventResponse)
def process_trial_queue_event(payload: TrialQueueEventRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialQueueEventResponse:
    return TrialService(db).handle_queue_event(payload, current_user=current_user)


@router.get("/trial/queue/zones/{zone_id}/studios", response_model=TrialZoneStudioQueuesResponse)
def get_trial_zone_studios(zone_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialZoneStudioQueuesResponse:
    return TrialService(db).get_zone_studio_queues(zone_id, current_user=current_user)


@router.get("/trial/queue/studios/{studio_id}/tokens", response_model=TrialStudioQueueResponse)
def get_trial_studio_queue(studio_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialStudioQueueResponse:
    return TrialService(db).get_studio_queue(studio_id, current_user=current_user)


@router.patch("/trial/queue/studios/{studio_id}/status", response_model=TrialStudioQueueResponse)
def update_trial_studio_status(studio_id: int, payload: TrialStudioStatusUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialStudioQueueResponse:
    return TrialService(db).update_studio_status(studio_id, payload, current_user=current_user)


@router.post("/trial/queue/tokens/{token_id}/start", response_model=TrialQueueEventResponse)
def start_trial_token(token_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialQueueEventResponse:
    return TrialService(db).start_token(token_id, current_user=current_user)


@router.post("/trial/queue/tokens/{token_id}/complete", response_model=TrialQueueEventResponse)
def complete_trial_token(token_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialQueueEventResponse:
    return TrialService(db).complete_token(token_id, current_user=current_user)


@router.post("/trial/queue/tokens/{token_id}/cancel", response_model=TrialQueueEventResponse)
def cancel_trial_token(token_id: int, payload: TrialTokenCancelRequest | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialQueueEventResponse:
    return TrialService(db).cancel_token(token_id, payload.cancellation_reason if payload else None, current_user=current_user)
