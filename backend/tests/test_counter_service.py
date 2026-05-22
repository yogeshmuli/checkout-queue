from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models.checkout_section import CheckoutSection, CheckoutSectionType
from app.models.counter import Counter, CounterType
from app.schemas.counter import CounterCreateRequest, CounterUpdateRequest
from app.services.counter_service import CounterService


class FakeCounterRepository:
    def __init__(self, db: object) -> None:
        self.sections = {
            1: CheckoutSection(id=1, store_id=1, name="Regular", section_type=CheckoutSectionType.REGULAR, is_active=True),
            2: CheckoutSection(id=2, store_id=1, name="Express", section_type=CheckoutSectionType.EXPRESS, is_active=True),
        }
        self.counters: dict[int, Counter] = {}
        self.next_id = 1

    def create_counter(self, counter: Counter) -> Counter:
        counter.id = self.next_id
        self.next_id += 1
        self.counters[counter.id] = counter
        return counter

    def list_counters(
        self,
        include_inactive: bool = False,
        store_id: int | None = None,
        section_id: int | None = None,
    ) -> list[Counter]:
        counters = list(self.counters.values())
        if not include_inactive:
            counters = [counter for counter in counters if counter.is_active]
        if section_id is not None:
            counters = [counter for counter in counters if counter.section_id == section_id]
        if store_id is not None:
            counters = [counter for counter in counters if self.sections[counter.section_id].store_id == store_id]
        return counters

    def get_counter_by_id(self, counter_id: int) -> Counter | None:
        return self.counters.get(counter_id)

    def get_section_by_id(self, section_id: int) -> CheckoutSection | None:
        return self.sections.get(section_id)

    def get_counter_by_section_and_name(self, section_id: int, name: str) -> Counter | None:
        for counter in self.counters.values():
            if counter.section_id == section_id and counter.name == name:
                return counter
        return None

    def commit(self) -> None:
        return None

    def refresh(self, instance: object) -> None:
        return None


@pytest.fixture
def counter_service(monkeypatch: pytest.MonkeyPatch) -> CounterService:
    fake_repository = FakeCounterRepository(None)

    def repository_factory(db: object) -> FakeCounterRepository:
        return fake_repository

    monkeypatch.setattr("app.services.counter_service.CounterRepository", repository_factory)
    return CounterService(None)


def test_create_counter(counter_service: CounterService) -> None:
    counter = counter_service.create_counter(
        CounterCreateRequest(
            section_id=1,
            counter_type=CounterType.REGULAR,
            name="Counter 1",
        )
    )

    assert counter.id == 1
    assert counter.counter_type == CounterType.REGULAR
    assert counter.name == "Counter 1"
    assert counter.is_active is True
    assert isinstance(counter.next_available_time, datetime)
    assert counter.next_available_time.tzinfo == timezone.utc


def test_create_counter_rejects_duplicate_name_per_section(counter_service: CounterService) -> None:
    payload = CounterCreateRequest(section_id=1, counter_type=CounterType.REGULAR, name="Counter 1")
    counter_service.create_counter(payload)

    with pytest.raises(HTTPException) as exc_info:
        counter_service.create_counter(payload)

    assert exc_info.value.status_code == 409


def test_update_counter_partially_updates_fields(counter_service: CounterService) -> None:
    counter = counter_service.create_counter(
        CounterCreateRequest(section_id=1, counter_type=CounterType.REGULAR, name="Counter 1")
    )

    updated_counter = counter_service.update_counter(
        counter.id,
        CounterUpdateRequest(section_id=2, counter_type=CounterType.EXPRESS, name="Counter 2"),
    )

    assert updated_counter.section_id == 2
    assert updated_counter.counter_type == CounterType.EXPRESS
    assert updated_counter.name == "Counter 2"


def test_delete_counter_soft_deletes(counter_service: CounterService) -> None:
    counter = counter_service.create_counter(
        CounterCreateRequest(section_id=1, counter_type=CounterType.REGULAR, name="Counter 1")
    )

    deleted_counter = counter_service.deactivate_counter(counter.id)

    assert deleted_counter.is_active is False
    assert counter_service.list_counters() == []
    assert counter_service.list_counters(include_inactive=True) == [deleted_counter]
