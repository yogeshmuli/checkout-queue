from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.trial_store_config import TrialStoreConfig
from app.repositories.trial_store_config_repository import TrialStoreConfigRepository
from app.schemas.trial_store_config import TrialStoreConfigUpdateRequest


class TrialStoreConfigService:
    def __init__(self, db: Session) -> None:
        self.repository = TrialStoreConfigRepository(db)

    def get_config(self, store_id: int) -> TrialStoreConfig:
        self._ensure_store_exists(store_id)
        config = self.repository.get_config(store_id)
        if config is None:
            config = TrialStoreConfig(store_id=store_id)
            self.repository.create(config)
            self.repository.commit()
            self.repository.refresh(config)
        return config

    def update_config(self, store_id: int, payload: TrialStoreConfigUpdateRequest) -> TrialStoreConfig:
        config = self.get_config(store_id)
        update_data = payload.model_dump()
        if update_data.get("token_id_prefix") is not None:
            update_data["token_id_prefix"] = update_data["token_id_prefix"].strip().upper() or None
        for field, value in update_data.items():
            setattr(config, field, value)
        self.repository.commit()
        self.repository.refresh(config)
        return config

    def _ensure_store_exists(self, store_id: int) -> None:
        if self.repository.get_store(store_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
