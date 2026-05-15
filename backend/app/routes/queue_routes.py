from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.schemas.queue import (
    CounterQueueResponse,
    CounterStatusUpdateRequest,
    QueueEventRequest,
    QueueEventResponse,
    QueueJoinRequest,
    QueueJoinResponse,
    QueueTokenResponse,
    TokenCancelRequest,
)
from app.services.queue_service import QueueService

router = APIRouter(prefix="/queue", tags=["queue"])

queue_event_roles = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_ADMIN,
    UserRole.MANAGER,
    UserRole.CASHIER,
)


@router.post("/join", response_model=QueueJoinResponse, status_code=201)
def join_queue(payload: QueueJoinRequest, db: Session = Depends(get_db)) -> QueueJoinResponse:
    return QueueService(db).join_queue(payload)


@router.post("/events", response_model=QueueEventResponse)
def process_queue_event(
    payload: QueueEventRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*queue_event_roles)),
) -> QueueEventResponse:
    return QueueService(db).handle_queue_event(payload)


@router.get("/status", response_model=QueueTokenResponse)
def get_token_status(
    token_id: int | None = None,
    store_id: int | None = None,
    phone_number: str | None = None,
    db: Session = Depends(get_db),
) -> QueueTokenResponse:
    return QueueService(db).get_token_status(token_id=token_id, store_id=store_id, phone_number=phone_number)


@router.get("/counters/{counter_id}/tokens", response_model=CounterQueueResponse)
def get_counter_queue(
    counter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*queue_event_roles)),
) -> CounterQueueResponse:
    return QueueService(db).get_counter_queue(counter_id)


@router.patch("/counters/{counter_id}/status", response_model=CounterQueueResponse)
def update_counter_status(
    counter_id: int,
    payload: CounterStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*queue_event_roles)),
) -> CounterQueueResponse:
    return QueueService(db).update_counter_status(counter_id, payload)


@router.post("/tokens/{token_id}/start", response_model=QueueEventResponse)
def start_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*queue_event_roles)),
) -> QueueEventResponse:
    return QueueService(db).start_token(token_id)


@router.post("/tokens/{token_id}/complete", response_model=QueueEventResponse)
def complete_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*queue_event_roles)),
) -> QueueEventResponse:
    return QueueService(db).complete_token(token_id)


@router.post("/tokens/{token_id}/cancel", response_model=QueueEventResponse)
def cancel_token(
    token_id: int,
    payload: TokenCancelRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*queue_event_roles)),
) -> QueueEventResponse:
    reason = payload.cancellation_reason if payload is not None else None
    return QueueService(db).cancel_token(token_id, reason)
