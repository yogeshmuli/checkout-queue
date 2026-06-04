import pytest
from pydantic import ValidationError

from app.models.store import Store
from app.models.store_config import StoreConfig
from app.schemas.store_config import StoreConfigUpdateRequest
from app.services.store_config_service import StoreConfigService


class FakeStoreConfigRepository:
    def __init__(self, db: object) -> None:
        self.stores = {
            1: Store(id=1, store_number="STORE-001", name="Main Store", is_active=True),
        }
        self.configs: dict[int, StoreConfig] = {}

    def get_store_by_id(self, store_id: int) -> Store | None:
        return self.stores.get(store_id)

    def get_config_by_store_id(self, store_id: int) -> StoreConfig | None:
        return self.configs.get(store_id)

    def create_config(self, config: StoreConfig) -> StoreConfig:
        config.id = len(self.configs) + 1
        if getattr(config, "default_item_count", None) is None:
            config.default_item_count = 10
        self.configs[config.store_id] = config
        return config

    def commit(self) -> None:
        return None

    def refresh(self, instance: object) -> None:
        return None


@pytest.fixture
def store_config_service(monkeypatch: pytest.MonkeyPatch) -> StoreConfigService:
    fake_repository = FakeStoreConfigRepository(None)

    def repository_factory(db: object) -> FakeStoreConfigRepository:
        return fake_repository

    monkeypatch.setattr("app.services.store_config_service.StoreConfigRepository", repository_factory)
    return StoreConfigService(None)


def test_get_store_config_creates_default_item_count(store_config_service: StoreConfigService) -> None:
    config = store_config_service.get_store_config(1)

    assert config.default_item_count == 10


def test_update_store_config_saves_default_item_count(store_config_service: StoreConfigService) -> None:
    config = store_config_service.upsert_store_config(
        1,
        StoreConfigUpdateRequest(
            token_id_prefix="bill",
            base_service_minutes=6,
            per_item_service_minutes=0.5,
            min_service_minutes=8,
            default_item_count=18,
        ),
    )

    assert config.token_id_prefix == "BILL"
    assert config.default_item_count == 18


def test_store_config_rejects_invalid_default_item_count() -> None:
    with pytest.raises(ValidationError):
        StoreConfigUpdateRequest(default_item_count=1001)
