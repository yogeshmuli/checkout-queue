from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.store import Store


class StoreRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_store(self, store: Store) -> Store:
        self.db.add(store)
        self.db.flush()
        return store

    def list_stores(self, include_inactive: bool = False) -> list[Store]:
        statement = select(Store).order_by(Store.id)
        if not include_inactive:
            statement = statement.where(Store.is_active.is_(True))
        return list(self.db.scalars(statement).all())

    def get_store_by_id(self, store_id: int) -> Store | None:
        return self.db.get(Store, store_id)

    def get_store_by_number(self, store_number: str) -> Store | None:
        statement = select(Store).where(Store.store_number == store_number)
        return self.db.scalar(statement)

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)

