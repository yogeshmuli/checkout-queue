from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.schemas.counter import CounterCreateRequest, CounterResponse, CounterUpdateRequest
from app.services.counter_service import CounterService

router = APIRouter(prefix="/counters", tags=["counters"])

counter_admin_roles = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_ADMIN,
    UserRole.MANAGER,
)


@router.post("", response_model=CounterResponse, status_code=201)
def create_counter(
    payload: CounterCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*counter_admin_roles)),
) -> CounterResponse:
    return CounterService(db).create_counter(payload)


@router.get("", response_model=list[CounterResponse])
def list_counters(
    include_inactive: bool = Query(default=False),
    store_id: int | None = Query(default=None),
    section_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*counter_admin_roles)),
) -> list[CounterResponse]:
    return CounterService(db).list_counters(
        include_inactive=include_inactive,
        store_id=store_id,
        section_id=section_id,
    )


@router.get("/{counter_id}", response_model=CounterResponse)
def get_counter(
    counter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*counter_admin_roles)),
) -> CounterResponse:
    return CounterService(db).get_counter(counter_id)


@router.patch("/{counter_id}", response_model=CounterResponse)
def update_counter(
    counter_id: int,
    payload: CounterUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*counter_admin_roles)),
) -> CounterResponse:
    return CounterService(db).update_counter(counter_id, payload)


@router.delete("/{counter_id}", response_model=CounterResponse)
def delete_counter(
    counter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*counter_admin_roles)),
) -> CounterResponse:
    return CounterService(db).deactivate_counter(counter_id)