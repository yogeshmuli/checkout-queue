from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.checkout_section import CheckoutSection
from app.repositories.section_repository import SectionRepository
from app.schemas.section import SectionCreateRequest, SectionUpdateRequest


class SectionService:
    def __init__(self, db: Session) -> None:
        self.repository = SectionRepository(db)

    def create_section(self, payload: SectionCreateRequest) -> CheckoutSection:
        store = self.repository.get_store_by_id(payload.store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

        existing = self.repository.get_section_by_store_and_name(payload.store_id, payload.name)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Section name already exists for this store")

        section = CheckoutSection(**payload.model_dump())
        self.repository.create_section(section)
        self.repository.commit()
        self.repository.refresh(section)
        return section

    def list_sections(self, include_inactive: bool = False, store_id: int | None = None) -> list[CheckoutSection]:
        return self.repository.list_sections(include_inactive=include_inactive, store_id=store_id)

    def get_section(self, section_id: int) -> CheckoutSection:
        section = self.repository.get_section_by_id(section_id)
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
        return section

    def update_section(self, section_id: int, payload: SectionUpdateRequest) -> CheckoutSection:
        section = self.get_section(section_id)
        update_data = payload.model_dump(exclude_unset=True)

        new_store_id = update_data.get("store_id", section.store_id)
        store = self.repository.get_store_by_id(new_store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

        new_name = update_data.get("name")
        if new_name is not None and (new_name != section.name or new_store_id != section.store_id):
            existing = self.repository.get_section_by_store_and_name(new_store_id, new_name)
            if existing is not None and existing.id != section.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Section name already exists for this store")

        for field, value in update_data.items():
            setattr(section, field, value)

        self.repository.commit()
        self.repository.refresh(section)
        return section

    def deactivate_section(self, section_id: int) -> CheckoutSection:
        section = self.get_section(section_id)
        section.is_active = False
        self.repository.commit()
        self.repository.refresh(section)
        return section
