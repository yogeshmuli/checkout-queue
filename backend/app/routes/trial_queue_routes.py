from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.trial_queue_token import TrialQueueTokenStatus
from app.models.user import User, UserRole
from app.schemas.trial_queue import (
    TrialQueueEventRequest,
    TrialQueueEventResponse,
    TrialQueueJoinRequest,
    TrialQueueJoinResponse,
    TrialQueueTokenResponse,
    TrialStoreResponse,
    TrialStudioQueueResponse,
    TrialStudioStatusUpdateRequest,
    TrialTokenCancelRequest,
    TrialTokenStartRequest,
    TrialZoneStudioQueuesResponse,
)
from app.services.trial_queue_service import TrialQueueService

router = APIRouter(tags=["trial-queue"])

trial_staff_roles = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_ADMIN,
    UserRole.MANAGER,
    UserRole.TRIAL_ZONE_ASSISTANT,
)


@router.get("/trial/queue/store-zones", response_model=list[TrialStoreResponse])
def list_trial_store_zones(db: Session = Depends(get_db)) -> list[TrialStoreResponse]:
    return TrialQueueService(db).list_store_zones()


@router.post("/trial/queue/join", response_model=TrialQueueJoinResponse)
def join_trial_queue(payload: TrialQueueJoinRequest, db: Session = Depends(get_db)) -> TrialQueueJoinResponse:
    return TrialQueueService(db).join_queue(payload)


@router.get("/trial/queue/status", response_model=TrialQueueTokenResponse)
def get_trial_token_status(token_id: int | None = None, store_id: int | None = None, phone_number: str | None = None, db: Session = Depends(get_db)) -> TrialQueueTokenResponse:
    return TrialQueueService(db).get_token_status(token_id=token_id, store_id=store_id, phone_number=phone_number)


@router.get("/trial/queue/tokens", response_model=list[TrialQueueTokenResponse])
def list_trial_queue_tokens(store_id: int | None = None, trial_zone_id: int | None = None, studio_id: int | None = None, status: TrialQueueTokenStatus | None = None, include_terminal: bool = Query(default=False), db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> list[TrialQueueTokenResponse]:
    return TrialQueueService(db).list_queue_tokens(store_id=store_id, trial_zone_id=trial_zone_id, studio_id=studio_id, token_status=status, include_terminal=include_terminal, current_user=current_user)


@router.post("/trial/queue/events", response_model=TrialQueueEventResponse)
def process_trial_queue_event(payload: TrialQueueEventRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialQueueEventResponse:
    return TrialQueueService(db).handle_queue_event(payload, current_user=current_user)


@router.get("/trial/queue/zones/{zone_id}/studios", response_model=TrialZoneStudioQueuesResponse)
def get_trial_zone_studios(zone_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialZoneStudioQueuesResponse:
    return TrialQueueService(db).get_zone_studio_queues(zone_id, current_user=current_user)


@router.post("/trial/queue/zones/{zone_id}/call-next", response_model=TrialQueueEventResponse)
def call_next_trial_token(zone_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialQueueEventResponse:
    return TrialQueueService(db).call_next_token_for_zone(zone_id, current_user=current_user)


@router.get("/trial/queue/studios/{studio_id}/tokens", response_model=TrialStudioQueueResponse)
def get_trial_studio_queue(studio_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialStudioQueueResponse:
    return TrialQueueService(db).get_studio_queue(studio_id, current_user=current_user)


@router.patch("/trial/queue/studios/{studio_id}/status", response_model=TrialStudioQueueResponse)
def update_trial_studio_status(studio_id: int, payload: TrialStudioStatusUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialStudioQueueResponse:
    return TrialQueueService(db).update_studio_status(studio_id, payload, current_user=current_user)


@router.post("/trial/queue/tokens/{token_id}/start", response_model=TrialQueueEventResponse)
def start_trial_token(token_id: int, payload: TrialTokenStartRequest, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialQueueEventResponse:
    return TrialQueueService(db).start_token(token_id, payload, current_user=current_user)


@router.post("/trial/queue/tokens/{token_id}/complete", response_model=TrialQueueEventResponse)
def complete_trial_token(token_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialQueueEventResponse:
    return TrialQueueService(db).complete_token(token_id, current_user=current_user)


@router.post("/trial/queue/tokens/{token_id}/cancel", response_model=TrialQueueEventResponse)
def cancel_trial_token(token_id: int, payload: TrialTokenCancelRequest | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_roles(*trial_staff_roles))) -> TrialQueueEventResponse:
    return TrialQueueService(db).cancel_token(token_id, payload.cancellation_reason if payload else None, current_user=current_user)


@router.post("/trial/queue/tokens/{token_id}/customer-cancel", response_model=TrialQueueEventResponse)
def customer_cancel_trial_token(token_id: int, db: Session = Depends(get_db)) -> TrialQueueEventResponse:
    return TrialQueueService(db).cancel_token_by_customer(token_id)


@router.post("/trial/queue/tokens/{token_id}/customer-move-last", response_model=TrialQueueTokenResponse)
def customer_move_trial_token_last(token_id: int, db: Session = Depends(get_db)) -> TrialQueueTokenResponse:
    return TrialQueueService(db).move_token_last_by_customer(token_id)
