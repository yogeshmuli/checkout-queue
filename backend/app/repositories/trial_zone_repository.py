from sqlalchemy import select

from app.models.trial_zone import TrialZone
from app.repositories.trial_base_repository import TrialBaseRepository


class TrialZoneRepository(TrialBaseRepository):
    def get_zone(self, zone_id: int) -> TrialZone | None:
        return self.db.get(TrialZone, zone_id)

    def get_zone_by_store_and_name(self, store_id: int, name: str) -> TrialZone | None:
        return self.db.scalar(select(TrialZone).where(TrialZone.store_id == store_id, TrialZone.name == name))

    def list_zones(self, include_inactive: bool = False, store_id: int | None = None) -> list[TrialZone]:
        statement = select(TrialZone).order_by(TrialZone.id.asc())
        if not include_inactive:
            statement = statement.where(TrialZone.is_active.is_(True))
        if store_id is not None:
            statement = statement.where(TrialZone.store_id == store_id)
        return list(self.db.scalars(statement).all())
