from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.trial_zone import TrialZone, TrialZoneType
from app.repositories.trial_zone_repository import TrialZoneRepository
from app.schemas.trial_zone import TrialZoneCreateRequest, TrialZoneUpdateRequest


class TrialZoneService:
    def __init__(self, db: Session) -> None:
        self.repository = TrialZoneRepository(db)

    def create_zone(self, payload: TrialZoneCreateRequest) -> TrialZone:
        self._ensure_store_exists(payload.store_id)
        name = payload.name.strip()
        if self.repository.get_zone_by_store_and_name(payload.store_id, name) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trial zone name already exists for this store")
        zone = TrialZone(
            store_id=payload.store_id,
            name=name,
            zone_type=TrialZoneType.REGULAR,
            gender=payload.gender,
            is_active=payload.is_active,
        )
        self.repository.create(zone)
        self.repository.commit()
        self.repository.refresh(zone)
        return zone

    def list_zones(self, include_inactive: bool = False, store_id: int | None = None) -> list[TrialZone]:
        return self.repository.list_zones(include_inactive=include_inactive, store_id=store_id)

    def get_zone(self, zone_id: int) -> TrialZone:
        zone = self.repository.get_zone(zone_id)
        if zone is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial zone not found")
        return zone

    def update_zone(self, zone_id: int, payload: TrialZoneUpdateRequest) -> TrialZone:
        zone = self.get_zone(zone_id)
        update_data = payload.model_dump(exclude_unset=True)
        store_id = update_data.get("store_id", zone.store_id)
        self._ensure_store_exists(store_id)
        if "name" in update_data:
            update_data["name"] = update_data["name"].strip()
            existing = self.repository.get_zone_by_store_and_name(store_id, update_data["name"])
            if existing is not None and existing.id != zone.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Trial zone name already exists for this store")
        for field, value in update_data.items():
            setattr(zone, field, value)
        self.repository.commit()
        self.repository.refresh(zone)
        return zone

    def deactivate_zone(self, zone_id: int) -> TrialZone:
        zone = self.get_zone(zone_id)
        zone.is_active = False
        self.repository.commit()
        self.repository.refresh(zone)
        return zone

    def _ensure_store_exists(self, store_id: int) -> None:
        if self.repository.get_store(store_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
