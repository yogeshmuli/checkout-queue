from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.authorization import authorized_store_ids, ensure_store_access
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.schemas.staff import StaffCreateRequest, StaffResponse, StaffUpdateRequest
from app.services.staff_service import StaffService

router = APIRouter(prefix="/staff", tags=["staff"])

staff_admin_roles = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_ADMIN,
    UserRole.MANAGER,
)


@router.post("", response_model=StaffResponse, status_code=201)
def create_staff(
    payload: StaffCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*staff_admin_roles)),
) -> StaffResponse:
    if payload.store_id is not None:
        ensure_store_access(db, current_user, payload.store_id)
    return StaffService(db).create_staff(payload)


@router.get("", response_model=list[StaffResponse])
def list_staff(
    include_inactive: bool = Query(default=False),
    store_id: int | None = Query(default=None),
    section_id: int | None = Query(default=None),
    counter_id: int | None = Query(default=None),
    zone_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*staff_admin_roles)),
) -> list[StaffResponse]:
    service = StaffService(db)
    if store_id is not None:
        ensure_store_access(db, current_user, store_id)
    service.ensure_assignment_resource_access(current_user, section_id, counter_id, zone_id)
    return service.list_staff(
        include_inactive=include_inactive,
        store_id=store_id,
        section_id=section_id,
        counter_id=counter_id,
        zone_id=zone_id,
        store_ids=authorized_store_ids(db, current_user),
    )


@router.get("/{staff_id}", response_model=StaffResponse)
def get_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*staff_admin_roles)),
) -> StaffResponse:
    staff = StaffService(db).get_staff(staff_id)
    if staff.store_id is not None:
        ensure_store_access(db, current_user, staff.store_id)
    return staff


@router.patch("/{staff_id}", response_model=StaffResponse)
def update_staff(
    staff_id: int,
    payload: StaffUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*staff_admin_roles)),
) -> StaffResponse:
    service = StaffService(db)
    staff = service.get_staff(staff_id)
    if staff.store_id is not None:
        ensure_store_access(db, current_user, staff.store_id)
    if payload.store_id is not None:
        ensure_store_access(db, current_user, payload.store_id)
    return service.update_staff(staff_id, payload)


@router.delete("/{staff_id}", response_model=StaffResponse)
def delete_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*staff_admin_roles)),
) -> StaffResponse:
    service = StaffService(db)
    staff = service.get_staff(staff_id)
    if staff.store_id is not None:
        ensure_store_access(db, current_user, staff.store_id)
    return service.deactivate_staff(staff_id)
