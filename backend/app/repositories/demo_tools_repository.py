from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.checkout_section import CheckoutSection
from app.models.counter import Counter
from app.models.ml_model_metadata import MLModelMetadata
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.models.store import Store
from app.models.trial import TrialQueueToken, TrialQueueTokenStatus, TrialStudio, TrialZone


class DemoToolsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_store_by_number(self, store_number: str) -> Store | None:
        return self.db.scalar(select(Store).where(Store.store_number == store_number))

    def create(self, instance):
        self.db.add(instance)
        self.db.flush()
        return instance

    def checkout_section_for_store(self, store_id: int) -> CheckoutSection | None:
        return self.db.scalar(select(CheckoutSection).where(CheckoutSection.store_id == store_id).order_by(CheckoutSection.id.asc()).limit(1))

    def checkout_counters_for_store(self, store_id: int) -> list[Counter]:
        statement = (
            select(Counter)
            .join(CheckoutSection, CheckoutSection.id == Counter.section_id)
            .where(CheckoutSection.store_id == store_id)
            .order_by(Counter.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def trial_zone_for_store(self, store_id: int) -> TrialZone | None:
        return self.db.scalar(select(TrialZone).where(TrialZone.store_id == store_id).order_by(TrialZone.id.asc()).limit(1))

    def trial_studios_for_store(self, store_id: int) -> list[TrialStudio]:
        statement = (
            select(TrialStudio)
            .join(TrialZone, TrialZone.id == TrialStudio.trial_zone_id)
            .where(TrialZone.store_id == store_id)
            .order_by(TrialStudio.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def count_checkout_completed_tokens(self, store_id: int) -> int:
        return self.db.scalar(
            select(func.count(QueueToken.id)).where(QueueToken.store_id == store_id, QueueToken.status == QueueTokenStatus.COMPLETED)
        ) or 0

    def count_checkout_terminal_tokens(self, store_id: int) -> int:
        return self.db.scalar(
            select(func.count(QueueToken.id)).where(
                QueueToken.store_id == store_id,
                QueueToken.status.in_((QueueTokenStatus.COMPLETED, QueueTokenStatus.CANCELLED, QueueTokenStatus.NO_SHOW)),
            )
        ) or 0

    def count_trial_completed_tokens(self, store_id: int) -> int:
        return self.db.scalar(
            select(func.count(TrialQueueToken.id)).where(TrialQueueToken.store_id == store_id, TrialQueueToken.status == TrialQueueTokenStatus.COMPLETED)
        ) or 0

    def count_trial_terminal_tokens(self, store_id: int) -> int:
        return self.db.scalar(
            select(func.count(TrialQueueToken.id)).where(
                TrialQueueToken.store_id == store_id,
                TrialQueueToken.status.in_((TrialQueueTokenStatus.COMPLETED, TrialQueueTokenStatus.CANCELLED, TrialQueueTokenStatus.NO_SHOW)),
            )
        ) or 0

    def count_ml_metadata(self, store_id: int) -> int:
        return self.db.scalar(select(func.count(MLModelMetadata.id)).where(MLModelMetadata.store_id == store_id)) or 0

    def delete_ml_metadata(self, store_id: int) -> None:
        self.db.execute(delete(MLModelMetadata).where(MLModelMetadata.store_id == store_id))

    def delete_store(self, store: Store) -> None:
        self.db.delete(store)
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)
