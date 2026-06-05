from sqlalchemy import select

from app.models.trial_studio import TrialStudio
from app.models.trial_zone import TrialZone
from app.repositories.trial_zone_repository import TrialZoneRepository


class TrialStudioRepository(TrialZoneRepository):
    def get_studio(self, studio_id: int) -> TrialStudio | None:
        return self.db.get(TrialStudio, studio_id)

    def get_studio_by_zone_and_name(self, zone_id: int, name: str) -> TrialStudio | None:
        return self.db.scalar(select(TrialStudio).where(TrialStudio.trial_zone_id == zone_id, TrialStudio.name == name))

    def list_studios(
        self,
        include_inactive: bool = False,
        store_id: int | None = None,
        trial_zone_id: int | None = None,
    ) -> list[TrialStudio]:
        statement = select(TrialStudio).join(TrialZone, TrialZone.id == TrialStudio.trial_zone_id).order_by(TrialStudio.id.asc())
        if not include_inactive:
            statement = statement.where(TrialStudio.is_active.is_(True))
        if store_id is not None:
            statement = statement.where(TrialZone.store_id == store_id)
        if trial_zone_id is not None:
            statement = statement.where(TrialStudio.trial_zone_id == trial_zone_id)
        return list(self.db.scalars(statement).all())

    def list_active_studios(self, store_id: int, trial_zone_id: int | None) -> list[TrialStudio]:
        statement = (
            select(TrialStudio)
            .join(TrialZone, TrialZone.id == TrialStudio.trial_zone_id)
            .where(
                TrialZone.store_id == store_id,
                TrialZone.is_active.is_(True),
                TrialStudio.is_active.is_(True),
            )
        )
        if trial_zone_id is not None:
            statement = statement.where(TrialStudio.trial_zone_id == trial_zone_id)
        return list(self.db.scalars(statement).all())
