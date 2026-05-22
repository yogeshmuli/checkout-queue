from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.store import Store
from app.models.store_config import StoreConfig


class StoreConfigRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_store_by_id(self, store_id: int) -> Store | None:
        return self.db.get(Store, store_id)

    def get_config_by_store_id(self, store_id: int) -> StoreConfig | None:
        statement = select(StoreConfig).where(StoreConfig.store_id == store_id)
        return self.db.scalar(statement)

    def create_config(self, config: StoreConfig) -> StoreConfig:
        self.db.add(config)
        self.db.flush()
        return config

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)
