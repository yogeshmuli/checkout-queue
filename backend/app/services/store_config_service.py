from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.store_config import StoreConfig
from app.repositories.store_config_repository import StoreConfigRepository
from app.schemas.store_config import StoreConfigUpdateRequest


class StoreConfigService:
    def __init__(self, db: Session) -> None:
        self.repository = StoreConfigRepository(db)

    def get_store_config(self, store_id: int) -> StoreConfig:
        self._ensure_store_exists(store_id)
        config = self.repository.get_config_by_store_id(store_id)
        if config is not None:
            return config

        config = StoreConfig(store_id=store_id)
        self.repository.create_config(config)
        self.repository.commit()
        self.repository.refresh(config)
        return config

    def upsert_store_config(self, store_id: int, payload: StoreConfigUpdateRequest) -> StoreConfig:
        self._ensure_store_exists(store_id)
        config = self.repository.get_config_by_store_id(store_id)
        if config is None:
            config = StoreConfig(store_id=store_id)
            self.repository.create_config(config)

        update_data = payload.model_dump()
        token_prefix = update_data.get("token_id_prefix")
        if token_prefix is not None:
            update_data["token_id_prefix"] = token_prefix.strip().upper() or None
        if update_data["shared_queue_enabled"] != config.shared_queue_enabled and len(self.repository.get_store_by_id(store_id).queue_tokens) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change shared_queue_enabled once set if there are existing queue tokens for the store",
            )
        for field, value in update_data.items():
            setattr(config, field, value)

        self.repository.commit()
        self.repository.refresh(config)
        return config

    def _ensure_store_exists(self, store_id: int) -> None:
        if self.repository.get_store_by_id(store_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
