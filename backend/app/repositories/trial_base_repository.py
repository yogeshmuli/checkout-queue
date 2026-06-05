from sqlalchemy.orm import Session

from app.models.store import Store


class TrialBaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_store(self, store_id: int) -> Store | None:
        return self.db.get(Store, store_id)

    def create(self, instance):
        self.db.add(instance)
        self.db.flush()
        return instance

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)

    def flush(self) -> None:
        self.db.flush()
