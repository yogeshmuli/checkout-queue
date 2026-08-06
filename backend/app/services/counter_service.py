import re
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.authorization import ensure_store_access
from app.models.user import User
from app.models.counter import Counter, CounterBasketSizeBand
from app.repositories.counter_repository import CounterRepository
from app.schemas.counter import CounterCreateRequest, CounterUpdateRequest


class CounterService:
    TOKEN_PREFIX_PATTERN = re.compile(r"^[A-Z0-9]+$")
    BASKET_SIZE_BANDS = {band.value for band in CounterBasketSizeBand}

    def __init__(self, db: Session) -> None:
        self.repository = CounterRepository(db)

    def create_counter(self, payload: CounterCreateRequest) -> Counter:
        section = self.repository.get_section_by_id(payload.section_id)
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")

        normalized_name = payload.name.strip() if payload.name else None
        normalized_token_prefix = self._normalize_token_prefix(payload.token_prefix)
        normalized_basket_size_bands = self._normalize_basket_size_bands(payload.basket_size_bands)
        if normalized_name:
            existing_counter = self.repository.get_counter_by_section_and_name(payload.section_id, normalized_name)
            if existing_counter is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Counter name already exists for this section")
        if normalized_token_prefix:
            existing_counter = self.repository.get_counter_by_section_and_token_prefix(payload.section_id, normalized_token_prefix)
            if existing_counter is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Counter token prefix already exists for this section")

        counter = Counter(
            section_id=payload.section_id,
            counter_type=payload.counter_type,
            name=normalized_name,
            token_prefix=normalized_token_prefix,
            basket_size_bands=normalized_basket_size_bands,
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
        store_ids: set[int] | None = None,
    ) -> list[Counter]:
        kwargs = dict(
            include_inactive=include_inactive,
            store_id=store_id,
            section_id=section_id,
        )
        if store_ids is not None:
            kwargs["store_ids"] = store_ids
        return self.repository.list_counters(**kwargs)

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

        if "name" in update_data:
            update_data["name"] = update_data["name"].strip() if update_data["name"] else None
        if "token_prefix" in update_data:
            update_data["token_prefix"] = self._normalize_token_prefix(update_data["token_prefix"])
        if "basket_size_bands" in update_data:
            update_data["basket_size_bands"] = self._normalize_basket_size_bands(update_data["basket_size_bands"])

        next_name = update_data.get("name", counter.name)
        if next_name:
            existing_counter = self.repository.get_counter_by_section_and_name(next_section_id, next_name)
            if existing_counter is not None and existing_counter.id != counter.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Counter name already exists for this section")

        next_token_prefix = update_data.get("token_prefix", counter.token_prefix)
        if next_token_prefix:
            existing_counter = self.repository.get_counter_by_section_and_token_prefix(next_section_id, next_token_prefix)
            if existing_counter is not None and existing_counter.id != counter.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Counter token prefix already exists for this section")

        for field, value in update_data.items():
            setattr(counter, field, value)

        self.repository.commit()
        self.repository.refresh(counter)
        return counter

    def _normalize_token_prefix(self, token_prefix: str | None) -> str | None:
        normalized = token_prefix.strip().upper() if token_prefix else None
        if not normalized:
            return None
        if not self.TOKEN_PREFIX_PATTERN.fullmatch(normalized):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Counter token prefix can contain only letters and numbers")
        return normalized

    def _normalize_basket_size_bands(
        self,
        basket_size_bands: list[CounterBasketSizeBand | str] | None,
    ) -> list[str] | None:
        if not basket_size_bands:
            return None

        normalized_bands: list[str] = []
        for band in basket_size_bands:
            value = band.value if isinstance(band, CounterBasketSizeBand) else str(band).strip().upper()
            if value not in self.BASKET_SIZE_BANDS:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid counter basket size band")
            if value not in normalized_bands:
                normalized_bands.append(value)

        return normalized_bands or None

    def deactivate_counter(self, counter_id: int) -> Counter:
        counter = self.get_counter(counter_id)
        counter.is_active = False
        self.repository.commit()
        self.repository.refresh(counter)
        return counter
    def ensure_counter_access(self, counter_id: int, current_user: User) -> None:
        counter = self.get_counter(counter_id)
        section = self.repository.get_section_by_id(counter.section_id)
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
        ensure_store_access(self.repository.db, current_user, section.store_id)

    def ensure_section_access(self, section_id: int, current_user: User) -> None:
        section = self.repository.get_section_by_id(section_id)
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
        ensure_store_access(self.repository.db, current_user, section.store_id)
