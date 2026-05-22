from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User, UserRole
from app.schemas.section import SectionCreateRequest, SectionResponse, SectionUpdateRequest
from app.services.section_service import SectionService

router = APIRouter(prefix="/sections", tags=["sections"])

section_admin_roles = (
    UserRole.SUPER_ADMIN,
    UserRole.STORE_ADMIN,
    UserRole.MANAGER,
)


@router.post("", response_model=SectionResponse, status_code=201)
def create_section(
    payload: SectionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*section_admin_roles)),
) -> SectionResponse:
    return SectionService(db).create_section(payload)


@router.get("", response_model=list[SectionResponse])
def list_sections(
    include_inactive: bool = Query(default=False),
    store_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*section_admin_roles)),
) -> list[SectionResponse]:
    return SectionService(db).list_sections(include_inactive=include_inactive, store_id=store_id)


@router.get("/{section_id}", response_model=SectionResponse)
def get_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*section_admin_roles)),
) -> SectionResponse:
    return SectionService(db).get_section(section_id)


@router.patch("/{section_id}", response_model=SectionResponse)
def update_section(
    section_id: int,
    payload: SectionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*section_admin_roles)),
) -> SectionResponse:
    return SectionService(db).update_section(section_id, payload)


@router.delete("/{section_id}", response_model=SectionResponse)
def delete_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*section_admin_roles)),
) -> SectionResponse:
    return SectionService(db).deactivate_section(section_id)
