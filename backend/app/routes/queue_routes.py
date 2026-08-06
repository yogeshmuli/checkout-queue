from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.authorization import authorized_store_ids, ensure_store_access
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.schemas.queue import (
    CounterQueueResponse,
    CounterStatusUpdateRequest,
    QueueEventRequest,
    QueueEventResponse,
    QueueJoinRequest,
    QueueJoinResponse,
    QueueStoreResponse,
    QueueTokenResponse,
    TokenCancelRequest,
)
from app.models.queue_token import QueueTokenStatus
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


@router.get("/store-sections", response_model=list[QueueStoreResponse])
def list_store_sections(db: Session = Depends(get_db)) -> list[QueueStoreResponse]:
    return QueueService(db).list_store_sections()


@router.get("/tokens", response_model=list[QueueTokenResponse])
def list_queue_tokens(
    store_id: int | None = None,
    section_id: int | None = None,
    counter_id: int | None = None,
    status: QueueTokenStatus | None = None,
    include_terminal: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*queue_event_roles)),
) -> list[QueueTokenResponse]:
    service = QueueService(db)
    if store_id is not None:
        ensure_store_access(db, current_user, store_id)
    if counter_id is not None:
        service.ensure_counter_access(counter_id, current_user)
    elif section_id is not None:
        service.ensure_section_access(section_id, current_user)
    return service.list_queue_tokens(
        store_id=store_id,
        section_id=section_id,
        counter_id=counter_id,
        token_status=status,
        include_terminal=include_terminal,
        store_ids=authorized_store_ids(db, current_user),
    )


@router.get("/counters/{counter_id}/tokens", response_model=CounterQueueResponse)
def get_counter_queue(
    counter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*queue_event_roles)),
) -> CounterQueueResponse:
    service = QueueService(db)
    service.ensure_counter_access(counter_id, current_user)
    return service.get_counter_queue(counter_id)


@router.patch("/counters/{counter_id}/status", response_model=CounterQueueResponse)
def update_counter_status(
    counter_id: int,
    payload: CounterStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*queue_event_roles)),
) -> CounterQueueResponse:
    service = QueueService(db)
    service.ensure_counter_access(counter_id, current_user)
    return service.update_counter_status(counter_id, payload)


@router.post("/counters/{counter_id}/call-next", response_model=QueueEventResponse)
def call_next_token_for_counter(
    counter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*queue_event_roles)),
) -> QueueEventResponse:
    service = QueueService(db)
    service.ensure_counter_access(counter_id, current_user)
    return service.call_next_token_for_counter(counter_id)


@router.post("/counters/{counter_id}/start-next", response_model=QueueEventResponse)
def start_next_token_for_counter(
    counter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*queue_event_roles)),
) -> QueueEventResponse:
    service = QueueService(db)
    service.ensure_counter_access(counter_id, current_user)
    return service.start_next_token_for_counter(counter_id)


@router.post("/tokens/{token_id}/start", response_model=QueueEventResponse)
def start_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*queue_event_roles)),
) -> QueueEventResponse:
    service = QueueService(db)
    service.ensure_token_access(token_id, current_user)
    return service.start_token(token_id)


@router.post("/tokens/{token_id}/complete", response_model=QueueEventResponse)
def complete_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*queue_event_roles)),
) -> QueueEventResponse:
    service = QueueService(db)
    service.ensure_token_access(token_id, current_user)
    return service.complete_token(token_id)


@router.post("/tokens/{token_id}/cancel", response_model=QueueEventResponse)
def cancel_token(
    token_id: int,
    payload: TokenCancelRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*queue_event_roles)),
) -> QueueEventResponse:
    reason = payload.cancellation_reason if payload is not None else None
    service = QueueService(db)
    service.ensure_token_access(token_id, current_user)
    return service.cancel_token(token_id, reason)


@router.post("/tokens/{token_id}/customer-cancel", response_model=QueueEventResponse)
def customer_cancel_token(
    token_id: int,
    db: Session = Depends(get_db),
) -> QueueEventResponse:
    return QueueService(db).cancel_token_by_customer(token_id)


@router.post("/tokens/{token_id}/customer-move-last", response_model=QueueTokenResponse)
def customer_move_token_last(
    token_id: int,
    db: Session = Depends(get_db),
) -> QueueTokenResponse:
    return QueueService(db).move_token_last_by_customer(token_id)
