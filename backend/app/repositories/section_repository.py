from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.checkout_section import CheckoutSection
from app.models.store import Store


class SectionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_section(self, section: CheckoutSection) -> CheckoutSection:
        self.db.add(section)
        self.db.flush()
        return section

    def list_sections(self, include_inactive: bool = False, store_id: int | None = None, store_ids: set[int] | None = None) -> list[CheckoutSection]:
        statement = select(CheckoutSection).order_by(CheckoutSection.id.asc())
        if not include_inactive:
            statement = statement.where(CheckoutSection.is_active.is_(True))
        if store_id is not None:
            statement = statement.where(CheckoutSection.store_id == store_id)
        elif store_ids is not None:
            if not store_ids:
                return []
            statement = statement.where(CheckoutSection.store_id.in_(store_ids))
        return list(self.db.scalars(statement).all())

    def get_section_by_id(self, section_id: int) -> CheckoutSection | None:
        return self.db.get(CheckoutSection, section_id)

    def get_store_by_id(self, store_id: int) -> Store | None:
        return self.db.get(Store, store_id)

    def get_section_by_store_and_name(self, store_id: int, name: str) -> CheckoutSection | None:
        statement = select(CheckoutSection).where(
            CheckoutSection.store_id == store_id,
            CheckoutSection.name == name,
        )
        return self.db.scalar(statement)

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)
