from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.trial_studio import TrialStudio
from app.repositories.trial_studio_repository import TrialStudioRepository
from app.schemas.trial_studio import TrialStudioCreateRequest, TrialStudioUpdateRequest
from app.services.trial_zone_service import TrialZoneService


class TrialStudioService(TrialZoneService):
    def __init__(self, db: Session) -> None:
        self.repository = TrialStudioRepository(db)

    def create_studio(self, payload: TrialStudioCreateRequest) -> TrialStudio:
        zone = self.get_zone(payload.trial_zone_id)
        name = payload.name.strip() if payload.name else None
        if name and self.repository.get_studio_by_zone_and_name(zone.id, name) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Studio name already exists for this trial zone")
        studio = TrialStudio(
            trial_zone_id=zone.id,
            name=name,
            studio_type=payload.studio_type,
            is_active=payload.is_active,
            next_available_time=datetime.now(timezone.utc),
        )
        self.repository.create(studio)
        self.repository.commit()
        self.repository.refresh(studio)
        return studio

    def list_studios(self, include_inactive: bool = False, store_id: int | None = None, trial_zone_id: int | None = None) -> list[TrialStudio]:
        return self.repository.list_studios(include_inactive=include_inactive, store_id=store_id, trial_zone_id=trial_zone_id)

    def get_studio(self, studio_id: int) -> TrialStudio:
        studio = self.repository.get_studio(studio_id)
        if studio is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Studio not found")
        return studio

    def update_studio(self, studio_id: int, payload: TrialStudioUpdateRequest) -> TrialStudio:
        studio = self.get_studio(studio_id)
        update_data = payload.model_dump(exclude_unset=True)
        zone_id = update_data.get("trial_zone_id", studio.trial_zone_id)
        self.get_zone(zone_id)
        if "name" in update_data:
            update_data["name"] = update_data["name"].strip() if update_data["name"] else None
            if update_data["name"]:
                existing = self.repository.get_studio_by_zone_and_name(zone_id, update_data["name"])
                if existing is not None and existing.id != studio.id:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Studio name already exists for this trial zone")
        for field, value in update_data.items():
            setattr(studio, field, value)
        self.repository.commit()
        self.repository.refresh(studio)
        return studio

    def deactivate_studio(self, studio_id: int) -> TrialStudio:
        studio = self.get_studio(studio_id)
        studio.is_active = False
        self.repository.commit()
        self.repository.refresh(studio)
        return studio
