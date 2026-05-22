import pytest
from fastapi import HTTPException

from app.models.checkout_section import CheckoutSection, CheckoutSectionType
from app.models.counter import Counter
from app.models.store import Store
from app.models.user import User, UserStoreAccess
from app.schemas.staff import StaffCreateRequest, StaffUpdateRequest
from app.services.staff_service import StaffService


class FakeStaffRepository:
    def __init__(self, db: object) -> None:
        self.users: dict[int, User] = {}
        self.stores: dict[int, Store] = {1: Store(id=1, store_number="S-001", name="Main Store")}
        self.sections: dict[int, CheckoutSection] = {
            1: CheckoutSection(id=1, store_id=1, name="Grocery", section_type=CheckoutSectionType.REGULAR)
        }
        self.counters: dict[int, Counter] = {1: Counter(id=1, section_id=1, counter_type="billing")}
        self.store_access: list[UserStoreAccess] = []
        self.next_id = 1
        self.next_access_id = 1
        self.committed = False

    def create_staff(self, user: User) -> User:
        user.id = self.next_id
        self.next_id += 1
        self.users[user.id] = user
        return user

    def list_staff(self, include_inactive: bool = False, store_id: int | None = None) -> list[User]:
        users = list(self.users.values())
        if not include_inactive:
            users = [user for user in users if user.is_active]
        if store_id is not None:
            users = [user for user in users if user.store_id == store_id]
        return users

    def get_staff_by_id(self, staff_id: int) -> User | None:
        return self.users.get(staff_id)

    def get_staff_by_email(self, email: str) -> User | None:
        for user in self.users.values():
            if user.email == email.lower():
                return user
        return None

    def get_staff_by_phone_number(self, phone_number: str) -> User | None:
        for user in self.users.values():
            if user.phone_number == phone_number:
                return user
        return None

    def get_store_by_id(self, store_id: int) -> Store | None:
        return self.stores.get(store_id)

    def get_section_by_id(self, section_id: int) -> CheckoutSection | None:
        return self.sections.get(section_id)

    def get_counter_by_id(self, counter_id: int) -> Counter | None:
        return self.counters.get(counter_id)

    def get_store_access(self, user_id: int, store_id: int) -> UserStoreAccess | None:
        for access in self.store_access:
            if access.user_id == user_id and access.store_id == store_id:
                return access
        return None

    def list_store_access(self, user_id: int) -> list[UserStoreAccess]:
        return [access for access in self.store_access if access.user_id == user_id]

    def add_store_access(self, access: UserStoreAccess) -> UserStoreAccess:
        access.id = self.next_access_id
        self.next_access_id += 1
        self.store_access.append(access)
        return access

    def commit(self) -> None:
        self.committed = True

    def refresh(self, instance: object) -> None:
        return None


@pytest.fixture
def staff_service(monkeypatch: pytest.MonkeyPatch) -> StaffService:
    fake_repository = FakeStaffRepository(None)

    def repository_factory(db: object) -> FakeStaffRepository:
        return fake_repository

    monkeypatch.setattr("app.services.staff_service.StaffRepository", repository_factory)
    return StaffService(None)


def test_create_staff_hashes_password_and_adds_store_access(staff_service: StaffService) -> None:
    user = staff_service.create_staff(
        StaffCreateRequest(
            email="Cashier@Example.com",
            password="strong-password",
            full_name="Cashier One",
            phone_number="9876543210",
            store_id=1,
            section_id=1,
            assigned_counter_id=1,
        )
    )

    assert user.id == 1
    assert user.email == "cashier@example.com"
    assert user.password_hash != "strong-password"
    assert staff_service.repository.store_access[0].user_id == user.id
    assert staff_service.repository.store_access[0].store_id == 1


def test_create_staff_rejects_duplicate_email(staff_service: StaffService) -> None:
    payload = StaffCreateRequest(email="cashier@example.com", password="strong-password", full_name="Cashier One")
    staff_service.create_staff(payload)

    with pytest.raises(HTTPException) as exc_info:
        staff_service.create_staff(payload)

    assert exc_info.value.status_code == 409


def test_update_staff_partially_updates_fields(staff_service: StaffService) -> None:
    user = staff_service.create_staff(
        StaffCreateRequest(email="cashier@example.com", password="strong-password", full_name="Cashier One")
    )

    updated_user = staff_service.update_staff(user.id, StaffUpdateRequest(full_name="Lead Cashier", store_id=1))

    assert updated_user.full_name == "Lead Cashier"
    assert updated_user.email == "cashier@example.com"
    assert updated_user.store_id == 1


def test_update_staff_rejects_mismatched_section_assignment(staff_service: StaffService) -> None:
    user = staff_service.create_staff(
        StaffCreateRequest(email="cashier@example.com", password="strong-password", full_name="Cashier One")
    )
    staff_service.repository.sections[2] = CheckoutSection(
        id=2,
        store_id=2,
        name="Other",
        section_type=CheckoutSectionType.REGULAR,
    )

    with pytest.raises(HTTPException) as exc_info:
        staff_service.update_staff(user.id, StaffUpdateRequest(store_id=1, section_id=2))

    assert exc_info.value.status_code == 400


def test_delete_staff_soft_deletes(staff_service: StaffService) -> None:
    user = staff_service.create_staff(
        StaffCreateRequest(email="cashier@example.com", password="strong-password", full_name="Cashier One")
    )

    deleted_user = staff_service.deactivate_staff(user.id)

    assert deleted_user.is_active is False
    assert staff_service.list_staff() == []
    assert staff_service.list_staff(include_inactive=True) == [deleted_user]
