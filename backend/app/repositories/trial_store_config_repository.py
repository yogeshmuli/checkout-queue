from sqlalchemy import select

from app.models.trial_store_config import TrialStoreConfig
from app.repositories.trial_base_repository import TrialBaseRepository


class TrialStoreConfigRepository(TrialBaseRepository):
    def get_config(self, store_id: int) -> TrialStoreConfig | None:
        return self.db.scalar(select(TrialStoreConfig).where(TrialStoreConfig.store_id == store_id))
