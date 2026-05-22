from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.counter import Counter
from app.repositories.counter_repository import CounterRepository
from app.schemas.counter import CounterCreateRequest, CounterUpdateRequest


class CounterService:
    def __init__(self, db: Session) -> None:
        self.repository = CounterRepository(db)

    def create_counter(self, payload: CounterCreateRequest) -> Counter:
        section = self.repository.get_section_by_id(payload.section_id)
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

        normalized_name = payload.name.strip() if payload.name else None
        if normalized_name:
            existing_counter = self.repository.get_counter_by_section_and_name(payload.section_id, normalized_name)
            if existing_counter is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Counter name already exists for this section")

        counter = Counter(
            section_id=payload.section_id,
            counter_type=payload.counter_type.strip(),
            name=normalized_name,
            is_active=payload.is_active,
            next_available_time=datetime.now(timezone.utc),
        )
        self.repository.create_counter(counter)
        self.repository.commit()
        self.repository.refresh(counter)
        return counter

    def list_counters(
        self,
        include_inactive: bool = False,
        store_id: int | None = None,
        section_id: int | None = None,
    ) -> list[Counter]:
        return self.repository.list_counters(
            include_inactive=include_inactive,
            store_id=store_id,
            section_id=section_id,
        )

    def get_counter(self, counter_id: int) -> Counter:
        counter = self.repository.get_counter_by_id(counter_id)
        if counter is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Counter not found")
        return counter

    def update_counter(self, counter_id: int, payload: CounterUpdateRequest) -> Counter:
        counter = self.get_counter(counter_id)
        update_data = payload.model_dump(exclude_unset=True)

        next_section_id = update_data.get("section_id", counter.section_id)
        section = self.repository.get_section_by_id(next_section_id)
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

        if "counter_type" in update_data and update_data["counter_type"] is not None:
            update_data["counter_type"] = update_data["counter_type"].strip()

        if "name" in update_data:
            update_data["name"] = update_data["name"].strip() if update_data["name"] else None

        next_name = update_data.get("name", counter.name)
        if next_name:
            existing_counter = self.repository.get_counter_by_section_and_name(next_section_id, next_name)
            if existing_counter is not None and existing_counter.id != counter.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Counter name already exists for this section")

        for field, value in update_data.items():
            setattr(counter, field, value)

        self.repository.commit()
        self.repository.refresh(counter)
        return counter

    def deactivate_counter(self, counter_id: int) -> Counter:
        counter = self.get_counter(counter_id)
        counter.is_active = False
        self.repository.commit()
        self.repository.refresh(counter)
        return counter