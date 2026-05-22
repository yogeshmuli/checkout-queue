from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
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
    return StaffService(db).create_staff(payload)


@router.get("", response_model=list[StaffResponse])
def list_staff(
    include_inactive: bool = Query(default=False),
    store_id: int | None = Query(default=None),
    section_id: int | None = Query(default=None),
    counter_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*staff_admin_roles)),
) -> list[StaffResponse]:
    return StaffService(db).list_staff(
        include_inactive=include_inactive,
        store_id=store_id,
        section_id=section_id,
        counter_id=counter_id,
    )


@router.get("/{staff_id}", response_model=StaffResponse)
def get_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*staff_admin_roles)),
) -> StaffResponse:
    return StaffService(db).get_staff(staff_id)


@router.patch("/{staff_id}", response_model=StaffResponse)
def update_staff(
    staff_id: int,
    payload: StaffUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*staff_admin_roles)),
) -> StaffResponse:
    return StaffService(db).update_staff(staff_id, payload)


@router.delete("/{staff_id}", response_model=StaffResponse)
def delete_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*staff_admin_roles)),
) -> StaffResponse:
    return StaffService(db).deactivate_staff(staff_id)
