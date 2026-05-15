import pytest
from fastapi import HTTPException

from app.models.store import Store
from app.schemas.store import StoreCreateRequest, StoreUpdateRequest
from app.services.store_service import StoreService


class FakeStoreRepository:
    def __init__(self, db: object) -> None:
        self.stores: dict[int, Store] = {}
        self.next_id = 1
        self.committed = False

    def create_store(self, store: Store) -> Store:
        store.id = self.next_id
        self.next_id += 1
        self.stores[store.id] = store
        return store

    def list_stores(self, include_inactive: bool = False) -> list[Store]:
        stores = list(self.stores.values())
        if not include_inactive:
            stores = [store for store in stores if store.is_active]
        return stores

    def get_store_by_id(self, store_id: int) -> Store | None:
        return self.stores.get(store_id)

    def get_store_by_number(self, store_number: str) -> Store | None:
        for store in self.stores.values():
            if store.store_number == store_number:
                return store
        return None

    def commit(self) -> None:
        self.committed = True

    def refresh(self, instance: object) -> None:
        return None


@pytest.fixture
def store_service(monkeypatch: pytest.MonkeyPatch) -> StoreService:
    fake_repository = FakeStoreRepository(None)

    def repository_factory(db: object) -> FakeStoreRepository:
        return fake_repository

    monkeypatch.setattr("app.services.store_service.StoreRepository", repository_factory)
    return StoreService(None)


def test_create_store(store_service: StoreService) -> None:
    store = store_service.create_store(
        StoreCreateRequest(
            store_number="STORE-001",
            name="Main Store",
            manager_phone="9876543210",
            spoc_phone="9876543211",
        )
    )

    assert store.id == 1
    assert store.store_number == "STORE-001"
    assert store.is_active


def test_create_store_rejects_duplicate_number(store_service: StoreService) -> None:
    payload = StoreCreateRequest(store_number="STORE-001", name="Main Store")
    store_service.create_store(payload)

    with pytest.raises(HTTPException) as exc_info:
        store_service.create_store(payload)

    assert exc_info.value.status_code == 409


def test_update_store_partially_updates_fields(store_service: StoreService) -> None:
    store = store_service.create_store(StoreCreateRequest(store_number="STORE-001", name="Main Store"))

    updated_store = store_service.update_store(store.id, StoreUpdateRequest(name="Updated Store"))

    assert updated_store.name == "Updated Store"
    assert updated_store.store_number == "STORE-001"


def test_delete_store_soft_deletes(store_service: StoreService) -> None:
    store = store_service.create_store(StoreCreateRequest(store_number="STORE-001", name="Main Store"))

    deleted_store = store_service.deactivate_store(store.id)

    assert deleted_store.is_active is False
    assert store_service.list_stores() == []
    assert store_service.list_stores(include_inactive=True) == [deleted_store]
