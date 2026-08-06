from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.checkout_section import CheckoutSection
from app.models.counter import Counter


class CounterRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_counter(self, counter: Counter) -> Counter:
        self.db.add(counter)
        self.db.flush()
        return counter

    def list_counters(
        self,
        include_inactive: bool = False,
        store_id: int | None = None,
        section_id: int | None = None,
        store_ids: set[int] | None = None,
    ) -> list[Counter]:
        statement = select(Counter).join(CheckoutSection, CheckoutSection.id == Counter.section_id).order_by(Counter.id.asc())
        if not include_inactive:
            statement = statement.where(Counter.is_active.is_(True))
        if store_id is not None:
            statement = statement.where(CheckoutSection.store_id == store_id)
        elif store_ids is not None:
            if not store_ids:
                return []
            statement = statement.where(CheckoutSection.store_id.in_(store_ids))
        if section_id is not None:
            statement = statement.where(Counter.section_id == section_id)
        return list(self.db.scalars(statement).all())

    def get_counter_by_id(self, counter_id: int) -> Counter | None:
        return self.db.get(Counter, counter_id)

    def get_section_by_id(self, section_id: int) -> CheckoutSection | None:
        return self.db.get(CheckoutSection, section_id)

    def get_counter_by_section_and_name(self, section_id: int, name: str) -> Counter | None:
        statement = select(Counter).where(
            Counter.section_id == section_id,
            Counter.name == name,
        )
        return self.db.scalar(statement)

    def get_counter_by_section_and_token_prefix(self, section_id: int, token_prefix: str) -> Counter | None:
        statement = select(Counter).where(
            Counter.section_id == section_id,
            Counter.token_prefix == token_prefix,
        )
        return self.db.scalar(statement)

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)
