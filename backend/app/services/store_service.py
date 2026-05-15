from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.store import Store
from app.repositories.store_repository import StoreRepository
from app.schemas.store import StoreCreateRequest, StoreUpdateRequest


class StoreService:
    def __init__(self, db: Session) -> None:
        self.repository = StoreRepository(db)

    def create_store(self, payload: StoreCreateRequest) -> Store:
        existing_store = self.repository.get_store_by_number(payload.store_number)
        if existing_store is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Store number already exists")

        store = Store(**payload.model_dump())
        self.repository.create_store(store)
        self.repository.commit()
        self.repository.refresh(store)
        return store

    def list_stores(self, include_inactive: bool = False) -> list[Store]:
        return self.repository.list_stores(include_inactive=include_inactive)

    def get_store(self, store_id: int) -> Store:
        store = self.repository.get_store_by_id(store_id)
        if store is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        return store

    def update_store(self, store_id: int, payload: StoreUpdateRequest) -> Store:
        store = self.get_store(store_id)
        update_data = payload.model_dump(exclude_unset=True)

        new_store_number = update_data.get("store_number")
        if new_store_number and new_store_number != store.store_number:
            existing_store = self.repository.get_store_by_number(new_store_number)
            if existing_store is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Store number already exists")

        for field, value in update_data.items():
            setattr(store, field, value)

        self.repository.commit()
        self.repository.refresh(store)
        return store

    def deactivate_store(self, store_id: int) -> Store:
        store = self.get_store(store_id)
        store.is_active = False
        self.repository.commit()
        self.repository.refresh(store)
        return store

