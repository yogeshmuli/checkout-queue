from sqlalchemy.orm import Session

from app.repositories.trial_repository import TrialRepository
from app.services.trial_calendar_service import TrialCalendarService
from app.services.trial_queue_service import TrialQueueService
from app.services.trial_store_config_service import TrialStoreConfigService
from app.services.trial_studio_service import TrialStudioService
from app.services.trial_zone_service import TrialZoneService


class TrialService(
    TrialQueueService,
    TrialCalendarService,
    TrialStoreConfigService,
    TrialStudioService,
    TrialZoneService,
):
    """Compatibility service exposing all Trial domain operations."""

    def __init__(self, db: Session) -> None:
        self.repository = TrialRepository(db)
