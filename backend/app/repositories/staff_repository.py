from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.checkout_section import CheckoutSection
from app.models.counter import Counter
from app.models.store import Store
from app.models.trial import TrialStudio, TrialZone
from app.models.user import User, UserStoreAccess


class StaffRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_staff(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def list_staff(
        self,
        include_inactive: bool = False,
        store_id: int | None = None,
        section_id: int | None = None,
        counter_id: int | None = None,
        studio_id: int | None = None,
    ) -> list[User]:
        statement = select(User).order_by(User.id.asc())
        if not include_inactive:
            statement = statement.where(User.is_active.is_(True))
        if store_id is not None:
            statement = statement.where(User.store_id == store_id)
        if section_id is not None:
            statement = statement.where(User.section_id == section_id)
        if counter_id is not None:
            statement = statement.where(User.assigned_counter_id == counter_id)
        if studio_id is not None:
            statement = statement.where(User.assigned_studio_id == studio_id)
        return list(self.db.scalars(statement).all())

    def get_staff_by_id(self, staff_id: int) -> User | None:
        return self.db.get(User, staff_id)

    def get_staff_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return self.db.scalar(statement)

    def get_staff_by_phone_number(self, phone_number: str) -> User | None:
        statement = select(User).where(User.phone_number == phone_number)
        return self.db.scalar(statement)

    def get_store_by_id(self, store_id: int) -> Store | None:
        return self.db.get(Store, store_id)

    def get_section_by_id(self, section_id: int) -> CheckoutSection | None:
        return self.db.get(CheckoutSection, section_id)

    def get_counter_by_id(self, counter_id: int) -> Counter | None:
        return self.db.get(Counter, counter_id)

    def get_studio_by_id(self, studio_id: int) -> TrialStudio | None:
        return self.db.get(TrialStudio, studio_id)

    def get_zone_by_id(self, zone_id: int) -> TrialZone | None:
        return self.db.get(TrialZone, zone_id)

    def get_store_access(self, user_id: int, store_id: int) -> UserStoreAccess | None:
        statement = select(UserStoreAccess).where(
            UserStoreAccess.user_id == user_id,
            UserStoreAccess.store_id == store_id,
        )
        return self.db.scalar(statement)

    def list_store_access(self, user_id: int) -> list[UserStoreAccess]:
        statement = select(UserStoreAccess).where(UserStoreAccess.user_id == user_id)
        return list(self.db.scalars(statement).all())

    def add_store_access(self, access: UserStoreAccess) -> UserStoreAccess:
        self.db.add(access)
        self.db.flush()
        return access

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)
