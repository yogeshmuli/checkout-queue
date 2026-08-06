from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.authorization import authorized_store_ids, ensure_store_access
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
    ensure_store_access(db, current_user, payload.store_id)
    return SectionService(db).create_section(payload)


@router.get("", response_model=list[SectionResponse])
def list_sections(
    include_inactive: bool = Query(default=False),
    store_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*section_admin_roles)),
) -> list[SectionResponse]:
    if store_id is not None:
        ensure_store_access(db, current_user, store_id)
    return SectionService(db).list_sections(include_inactive=include_inactive, store_id=store_id, store_ids=authorized_store_ids(db, current_user))


@router.get("/{section_id}", response_model=SectionResponse)
def get_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*section_admin_roles)),
) -> SectionResponse:
    section = SectionService(db).get_section(section_id)
    ensure_store_access(db, current_user, section.store_id)
    return section


@router.patch("/{section_id}", response_model=SectionResponse)
def update_section(
    section_id: int,
    payload: SectionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*section_admin_roles)),
) -> SectionResponse:
    service = SectionService(db)
    section = service.get_section(section_id)
    ensure_store_access(db, current_user, section.store_id)
    if payload.store_id is not None:
        ensure_store_access(db, current_user, payload.store_id)
    return service.update_section(section_id, payload)


@router.delete("/{section_id}", response_model=SectionResponse)
def delete_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*section_admin_roles)),
) -> SectionResponse:
    service = SectionService(db)
    section = service.get_section(section_id)
    ensure_store_access(db, current_user, section.store_id)
    return service.deactivate_section(section_id)
