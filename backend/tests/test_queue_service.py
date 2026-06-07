import pytest
from fastapi import HTTPException
from datetime import datetime, time, timedelta, timezone

from app.models.calendar import StoreCalendarDay, StoreHoliday
from app.models.checkout_section import CheckoutSection, CheckoutSectionType
from app.models.counter import Counter
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.models.store import Store
from app.models.store_config import StoreConfig
from app.schemas.queue import QueueEventRequest, QueueEventType, QueueJoinRequest
from app.services.queue_service import QueueService


class FakeQueueRepository:
    def __init__(self, db: object) -> None:
        self.stores = {
            1: Store(id=1, store_number="STORE-001", name="Main Store", is_active=True),
            2: Store(id=2, store_number="STORE-002", name="Inactive Store", is_active=False),
        }
        self.sections = {
            1: CheckoutSection(
                id=1,
                store_id=1,
                name="Regular",
                section_type=CheckoutSectionType.REGULAR,
                is_active=True,
            ),
            2: CheckoutSection(
                id=2,
                store_id=1,
                name="Inactive",
                section_type=CheckoutSectionType.REGULAR,
                is_active=False,
            ),
        }
        self.tokens: list[QueueToken] = []
        self.store_configs: dict[int, StoreConfig] = {}
        self.ml_model_metadata = {}
        self.calendar_days: dict[int, list[StoreCalendarDay]] = {}
        self.holidays: dict[tuple[int, object], StoreHoliday] = {}
        now = datetime.now(timezone.utc)
        self.counters = [
            Counter(id=1, section_id=1, counter_type="regular", name="C1", token_prefix="C1", is_active=True, next_available_time=now),
            Counter(id=2, section_id=1, counter_type="regular", name="C2", token_prefix="C2", is_active=True, next_available_time=now),
        ]

    def get_store(self, store_id: int) -> Store | None:
        return self.stores.get(store_id)

    def get_store_config(self, store_id: int) -> StoreConfig | None:
        return self.store_configs.get(store_id)

    def get_ready_ml_model_metadata(self, store_id: int):
        return self.ml_model_metadata.get(store_id)

    def list_calendar_days(self, store_id: int) -> list[StoreCalendarDay]:
        return self.calendar_days.get(store_id, [])

    def get_active_holiday(self, store_id: int, holiday_date) -> StoreHoliday | None:
        return self.holidays.get((store_id, holiday_date))

    def get_section(self, section_id: int) -> CheckoutSection | None:
        return self.sections.get(section_id)

    def get_counter(self, counter_id: int) -> Counter | None:
        for counter in self.counters:
            if counter.id == counter_id:
                return counter
        return None

    def get_token(self, token_id: int) -> QueueToken | None:
        for token in self.tokens:
            if token.id == token_id:
                return token
        return None

    def get_active_token_for_phone(self, store_id: int, phone_number: str) -> QueueToken | None:
        for token in self.tokens:
            if (
                token.store_id == store_id
                and token.phone_number == phone_number
                and token.status in (QueueTokenStatus.WAITING, QueueTokenStatus.CALLED, QueueTokenStatus.SERVING)
            ):
                return token
        return None

    def list_waiting_tokens(self, counter_id: int) -> list[QueueToken]:
        waiting = [
            token
            for token in self.tokens
            if token.assigned_counter_id == counter_id and token.status == QueueTokenStatus.WAITING
        ]
        max_dt = datetime.max.replace(tzinfo=timezone.utc)
        return sorted(waiting, key=lambda token: ((token.calling_time or max_dt), token.id or 0))

    def list_shared_waiting_tokens(self, store_id: int, section_id: int) -> list[QueueToken]:
        waiting = [
            token
            for token in self.tokens
            if (
                token.store_id == store_id
                and token.section_id == section_id
                and token.assigned_counter_id is None
                and token.status == QueueTokenStatus.WAITING
            )
        ]
        max_dt = datetime.max.replace(tzinfo=timezone.utc)
        return sorted(waiting, key=lambda token: ((token.created_at or max_dt), token.id or 0))

    def get_current_serving_customer_for_counter(self, counter_id: int) -> QueueToken | None:
        serving = [
            token
            for token in self.tokens
            if token.assigned_counter_id == counter_id and token.status == QueueTokenStatus.SERVING
        ]
        if not serving:
            return None
        return sorted(
            serving,
            key=lambda token: ((token.service_started_at or datetime.min.replace(tzinfo=timezone.utc)), token.id or 0),
            reverse=True,
        )[0]

    def get_current_called_customer_for_counter(self, counter_id: int) -> QueueToken | None:
        called = [
            token
            for token in self.tokens
            if token.assigned_counter_id == counter_id and token.status == QueueTokenStatus.CALLED
        ]
        if not called:
            return None
        return sorted(
            called,
            key=lambda token: ((token.called_at or datetime.min.replace(tzinfo=timezone.utc)), token.id or 0),
            reverse=True,
        )[0]

    def count_tokens_for_numbering(self, counter_id: int) -> int:
        return len([token for token in self.tokens if token.assigned_counter_id == counter_id])

    def count_shared_tokens_for_numbering(self, store_id: int, section_id: int) -> int:
        return len([
            token
            for token in self.tokens
            if token.store_id == store_id and token.section_id == section_id and "-Q-" in (token.token_number or "")
        ])

    def list_tokens_for_counter(self, counter_id: int) -> list[QueueToken]:
        tokens = [
            token
            for token in self.tokens
            if (
                token.assigned_counter_id == counter_id
                and token.status in (QueueTokenStatus.WAITING, QueueTokenStatus.CALLED, QueueTokenStatus.SERVING)
            )
        ]
        max_dt = datetime.max.replace(tzinfo=timezone.utc)
        return sorted(tokens, key=lambda token: ((token.calling_time or max_dt), token.id or 0))

    def list_active_counters(self, store_id: int, section_id: int | None) -> list[Counter]:
        section = self.sections.get(section_id) if section_id is not None else None
        if section_id is not None and (section is None or section.store_id != store_id or not section.is_active):
            return []
        if section_id is None:
            store_section_ids = {s.id for s in self.sections.values() if s.store_id == store_id and s.is_active}
            return [counter for counter in self.counters if counter.is_active and counter.section_id in store_section_ids]
        return [counter for counter in self.counters if counter.is_active and counter.section_id == section_id]

    def create_token(self, token: QueueToken) -> QueueToken:
        token.id = len(self.tokens) + 1
        self.tokens.append(token)
        return token

    def commit(self) -> None:
        return None

    def refresh(self, instance: object) -> None:
        return None


def make_store_config(token_id_prefix: str | None, shared_queue_enabled: bool = False) -> StoreConfig:
    return StoreConfig(
        store_id=1,
        token_id_prefix=token_id_prefix,
        base_service_minutes=4,
        per_item_service_minutes=0.25,
        min_service_minutes=5,
        default_item_count=10,
        shared_queue_enabled=shared_queue_enabled,
    )


@pytest.fixture
def queue_service(monkeypatch: pytest.MonkeyPatch) -> QueueService:
    fake_repository = FakeQueueRepository(None)

    def repository_factory(db: object) -> FakeQueueRepository:
        return fake_repository

    monkeypatch.setattr("app.services.queue_service.QueueRepository", repository_factory)
    return QueueService(None)


def test_join_queue_creates_waiting_token(queue_service: QueueService) -> None:
    response = queue_service.join_queue(
        QueueJoinRequest(
            store_id=1,
            section_id=1,
            phone_number="9876543210",
            item_count=12,
            basket_size="medium",
            cart_type="basket",
            is_still_shopping=True,
            customer_type="regular",
        )
    )

    assert response.token_id == 1
    assert response.token_number == "S1-C1-001"
    assert response.position == 1
    assert response.estimated_wait_minutes == 0
    assert response.calculation_method == "RULE_BASED"


def test_join_queue_rejects_duplicate_active_token(queue_service: QueueService) -> None:
    payload = QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210")
    queue_service.join_queue(payload)

    with pytest.raises(HTTPException) as exc_info:
        queue_service.join_queue(payload)

    assert exc_info.value.status_code == 409


def test_join_queue_uses_store_config_for_prefix_and_service_time(queue_service: QueueService) -> None:
    queue_service.repository.counters = [queue_service.repository.counters[0]]
    queue_service.repository.store_configs[1] = StoreConfig(
        store_id=1,
        token_id_prefix="BILL",
        base_service_minutes=2,
        per_item_service_minutes=1.5,
        min_service_minutes=3,
    )

    response = queue_service.join_queue(
        QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210", item_count=4)
    )

    token = queue_service.repository.tokens[0]
    assert response.token_number == "BILL-C1-001"
    assert token.service_time_minutes == 8


def test_join_queue_falls_back_to_counter_id_prefix(queue_service: QueueService) -> None:
    queue_service.repository.counters = [queue_service.repository.counters[0]]
    queue_service.repository.counters[0].token_prefix = None
    queue_service.repository.store_configs[1] = make_store_config("BILL")

    response = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210"))

    assert response.token_number == "BILL-C1-001"


def test_join_queue_falls_back_to_legacy_store_prefix(queue_service: QueueService) -> None:
    queue_service.repository.counters = [queue_service.repository.counters[0]]

    response = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210"))

    assert response.token_number == "S1-C1-001"


def test_join_queue_sequence_is_independent_per_counter(queue_service: QueueService) -> None:
    queue_service.repository.store_configs[1] = make_store_config("BILL")

    first = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210", item_count=1))
    second = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=1))
    third = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543212", item_count=1))

    assert first.token_number == "BILL-C1-001"
    assert second.token_number == "BILL-C2-001"
    assert third.token_number == "BILL-C1-002"


def test_shared_queue_requires_section(queue_service: QueueService) -> None:
    queue_service.repository.store_configs[1] = make_store_config("BILL", shared_queue_enabled=True)

    with pytest.raises(HTTPException) as exc_info:
        queue_service.join_queue(QueueJoinRequest(store_id=1, phone_number="9876543210", item_count=1))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Section is required for shared queue stores"


def test_shared_queue_join_creates_unassigned_section_token(queue_service: QueueService) -> None:
    queue_service.repository.store_configs[1] = make_store_config("BILL", shared_queue_enabled=True)

    response = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210", item_count=1))
    token = queue_service.repository.tokens[0]

    assert response.token_number == "BILL-Q-001"
    assert response.assigned_counter_id is None
    assert token.assigned_counter_id is None
    assert response.position == 1
    assert token.calling_time is not None


def test_shared_queue_schedules_by_earliest_eligible_counter(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.store_configs[1] = make_store_config("BILL", shared_queue_enabled=True)
    queue_service.repository.counters = [
        Counter(id=1, section_id=1, counter_type="regular", name="Small", token_prefix="SML", basket_size_bands=["SMALL"], is_active=True, next_available_time=now),
        Counter(id=2, section_id=1, counter_type="regular", name="Large", token_prefix="LRG", basket_size_bands=["LARGE"], is_active=True, next_available_time=now),
    ]

    small = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210", item_count=5))
    large = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=25))

    assert small.assigned_counter_id is None
    assert large.assigned_counter_id is None
    assert queue_service.repository.tokens[0].calling_time is not None
    assert queue_service.repository.tokens[1].calling_time is not None
    assert queue_service.repository.counters[0].next_available_time > queue_service.repository.tokens[0].calling_time
    assert queue_service.repository.counters[1].next_available_time > queue_service.repository.tokens[1].calling_time


def test_shared_queue_position_is_section_wide(queue_service: QueueService) -> None:
    queue_service.repository.counters = [queue_service.repository.counters[0]]
    queue_service.repository.store_configs[1] = make_store_config("BILL", shared_queue_enabled=True)

    first = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210", item_count=1))
    second = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=1))

    assert first.position == 1
    assert second.position == 2
    assert queue_service.get_token_status(token_id=second.token_id).position == 2


def test_shared_queue_staff_pull_assigns_counter(queue_service: QueueService) -> None:
    queue_service.repository.store_configs[1] = make_store_config("BILL", shared_queue_enabled=True)
    created = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210", item_count=1))

    response = queue_service.start_next_token_for_counter(2)
    token = queue_service.repository.get_token(created.token_id)
    next_created = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=1))

    assert response.status == QueueTokenStatus.SERVING
    assert response.assigned_counter_id == 2
    assert token.assigned_counter_id == 2
    assert next_created.token_number == "BILL-Q-002"


def test_join_queue_rejects_when_store_calendar_is_closed_today(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.calendar_days[1] = [
        StoreCalendarDay(
            store_id=1,
            weekday=now.weekday(),
            is_open=False,
            open_time=time(0, 0),
            close_time=time(23, 59),
            timezone="UTC",
        )
    ]

    with pytest.raises(HTTPException) as exc_info:
        queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210"))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Store is closed for queue joining"


def test_join_queue_rejects_when_today_is_active_holiday(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.calendar_days[1] = [
        StoreCalendarDay(
            store_id=1,
            weekday=now.weekday(),
            is_open=True,
            open_time=time(0, 0),
            close_time=time(23, 59),
            timezone="UTC",
        )
    ]
    queue_service.repository.holidays[(1, now.date())] = StoreHoliday(
        store_id=1,
        holiday_date=now.date(),
        name="Closed",
        is_active=True,
    )

    with pytest.raises(HTTPException) as exc_info:
        queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210"))

    assert exc_info.value.status_code == 409


def test_join_queue_rejects_inactive_store(queue_service: QueueService) -> None:
    with pytest.raises(HTTPException) as exc_info:
        queue_service.join_queue(QueueJoinRequest(store_id=2, section_id=1, phone_number="9876543210"))

    assert exc_info.value.status_code == 404


def test_join_queue_rejects_inactive_section(queue_service: QueueService) -> None:
    with pytest.raises(HTTPException) as exc_info:
        queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=2, phone_number="9876543210"))

    assert exc_info.value.status_code == 404


def test_join_queue_wait_time_uses_waiting_tokens_ahead_and_counter_count(queue_service: QueueService) -> None:
    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210", item_count=1))
    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=1))

    response = queue_service.join_queue(
        QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543212", item_count=1)
    )

    assert response.position == 2
    assert response.estimated_wait_minutes == 5


def test_join_queue_wait_time_uses_item_counts_of_people_ahead(queue_service: QueueService) -> None:
    queue_service.repository.counters = [queue_service.repository.counters[0]]
    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210", item_count=1))
    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=20))

    response = queue_service.join_queue(
        QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543212", item_count=1)
    )

    assert response.position == 3
    assert response.estimated_wait_minutes == 14


def test_join_queue_rejects_when_no_active_counter(queue_service: QueueService) -> None:
    queue_service.repository.counters = []

    with pytest.raises(HTTPException) as exc_info:
        queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=1))

    assert exc_info.value.status_code == 503


def test_join_queue_filters_counters_by_small_basket_band(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.counters = [
        Counter(id=1, section_id=1, counter_type="regular", name="Small", token_prefix="SML", basket_size_bands=["SMALL"], is_active=True, next_available_time=now + timedelta(minutes=10)),
        Counter(id=2, section_id=1, counter_type="regular", name="Medium", token_prefix="MED", basket_size_bands=["MEDIUM"], is_active=True, next_available_time=now),
    ]

    response = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=9))

    assert response.assigned_counter_id == 1


def test_join_queue_explicit_item_count_wins_over_basket_size(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.counters = [
        Counter(id=1, section_id=1, counter_type="regular", name="Small", token_prefix="SML", basket_size_bands=["SMALL"], is_active=True, next_available_time=now),
        Counter(id=2, section_id=1, counter_type="regular", name="Large", token_prefix="LRG", basket_size_bands=["LARGE"], is_active=True, next_available_time=now),
    ]

    response = queue_service.join_queue(
        QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=5, basket_size="large")
    )
    token = queue_service.repository.tokens[0]

    assert response.assigned_counter_id == 1
    assert token.item_count == 5
    assert token.basket_size == "large"


def test_join_queue_derives_small_item_count_from_basket_size(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.counters = [
        Counter(id=1, section_id=1, counter_type="regular", name="Small", token_prefix="SML", basket_size_bands=["SMALL"], is_active=True, next_available_time=now),
    ]

    response = queue_service.join_queue(
        QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", basket_size="Small")
    )

    assert response.assigned_counter_id == 1
    assert queue_service.repository.tokens[0].item_count == 9


def test_join_queue_filters_counters_by_medium_boundaries(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.counters = [
        Counter(id=1, section_id=1, counter_type="regular", name="Small", token_prefix="SML", basket_size_bands=["SMALL"], is_active=True, next_available_time=now),
        Counter(id=2, section_id=1, counter_type="regular", name="Medium", token_prefix="MED", basket_size_bands=["MEDIUM"], is_active=True, next_available_time=now),
    ]

    first = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=10))
    second = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543212", item_count=20))

    assert first.assigned_counter_id == 2
    assert second.assigned_counter_id == 2


def test_join_queue_derives_medium_item_count_from_basket_size(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.counters = [
        Counter(id=1, section_id=1, counter_type="regular", name="Medium", token_prefix="MED", basket_size_bands=["MEDIUM"], is_active=True, next_available_time=now),
    ]

    response = queue_service.join_queue(
        QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", basket_size="medium")
    )

    assert response.assigned_counter_id == 1
    assert queue_service.repository.tokens[0].item_count == 20


def test_join_queue_filters_counters_by_large_basket_band(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.counters = [
        Counter(id=1, section_id=1, counter_type="regular", name="Medium", token_prefix="MED", basket_size_bands=["MEDIUM"], is_active=True, next_available_time=now),
        Counter(id=2, section_id=1, counter_type="regular", name="Large", token_prefix="LRG", basket_size_bands=["LARGE"], is_active=True, next_available_time=now + timedelta(minutes=10)),
    ]

    response = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=21))

    assert response.assigned_counter_id == 2


def test_join_queue_derives_large_item_count_from_basket_size(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.counters = [
        Counter(id=1, section_id=1, counter_type="regular", name="Large", token_prefix="LRG", basket_size_bands=["LARGE"], is_active=True, next_available_time=now),
    ]

    response = queue_service.join_queue(
        QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", basket_size="large")
    )

    assert response.assigned_counter_id == 1
    assert queue_service.repository.tokens[0].item_count == 30


def test_join_queue_allows_multi_band_counter(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.counters = [
        Counter(id=1, section_id=1, counter_type="regular", name="Flexible", token_prefix="FLEX", basket_size_bands=["SMALL", "MEDIUM"], is_active=True, next_available_time=now),
        Counter(id=2, section_id=1, counter_type="regular", name="Large", token_prefix="LRG", basket_size_bands=["LARGE"], is_active=True, next_available_time=now),
    ]

    small = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=2))
    medium = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543212", item_count=15))

    assert small.assigned_counter_id == 1
    assert medium.assigned_counter_id == 1


def test_join_queue_missing_item_count_uses_only_unrestricted_counters(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.counters = [
        Counter(id=1, section_id=1, counter_type="regular", name="Small", token_prefix="SML", basket_size_bands=["SMALL"], is_active=True, next_available_time=now),
        Counter(id=2, section_id=1, counter_type="regular", name="Any", token_prefix="ANY", basket_size_bands=None, is_active=True, next_available_time=now + timedelta(minutes=10)),
    ]

    response = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211"))

    assert response.assigned_counter_id == 2


def test_join_queue_rejects_when_no_counter_matches_basket_size(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.counters = [
        Counter(id=1, section_id=1, counter_type="regular", name="Small", token_prefix="SML", basket_size_bands=["SMALL"], is_active=True, next_available_time=now),
    ]

    with pytest.raises(HTTPException) as exc_info:
        queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=12))

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "No active counters available for this basket size"


def test_join_queue_still_shopping_uses_store_default_item_count(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.store_configs[1] = StoreConfig(
        store_id=1,
        token_id_prefix=None,
        base_service_minutes=4,
        per_item_service_minutes=1,
        min_service_minutes=5,
        default_item_count=18,
    )
    queue_service.repository.counters = [
        Counter(id=1, section_id=1, counter_type="regular", name="Small", token_prefix="SML", basket_size_bands=["SMALL"], is_active=True, next_available_time=now),
        Counter(id=2, section_id=1, counter_type="regular", name="Medium", token_prefix="MED", basket_size_bands=["MEDIUM"], is_active=True, next_available_time=now),
    ]

    response = queue_service.join_queue(
        QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", is_still_shopping=True)
    )
    token = queue_service.repository.tokens[0]

    assert response.assigned_counter_id == 2
    assert token.item_count == 18
    assert token.service_time_minutes == 22


def test_join_queue_missing_items_and_basket_not_still_shopping_stays_null(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.counters = [
        Counter(id=1, section_id=1, counter_type="regular", name="Small", token_prefix="SML", basket_size_bands=["SMALL"], is_active=True, next_available_time=now),
        Counter(id=2, section_id=1, counter_type="regular", name="Any", token_prefix="ANY", basket_size_bands=None, is_active=True, next_available_time=now),
    ]

    response = queue_service.join_queue(
        QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", is_still_shopping=False)
    )

    assert response.assigned_counter_id == 2
    assert queue_service.repository.tokens[0].item_count is None


def test_join_queue_earliest_eligible_counter_still_wins(queue_service: QueueService) -> None:
    now = datetime.now(timezone.utc)
    queue_service.repository.counters = [
        Counter(id=1, section_id=1, counter_type="regular", name="Busy Medium", token_prefix="M1", basket_size_bands=["MEDIUM"], is_active=True, next_available_time=now),
        Counter(id=2, section_id=1, counter_type="regular", name="Early Medium", token_prefix="M2", basket_size_bands=["MEDIUM"], is_active=True, next_available_time=now),
        Counter(id=3, section_id=1, counter_type="regular", name="Small", token_prefix="S1", basket_size_bands=["SMALL"], is_active=True, next_available_time=now - timedelta(minutes=10)),
    ]
    queue_service.repository.tokens.append(
        QueueToken(
            id=1,
            store_id=1,
            section_id=1,
            assigned_counter_id=1,
            token_number="BUSY",
            phone_number="9876543200",
            status=QueueTokenStatus.SERVING,
            item_count=50,
            service_time_minutes=30,
            service_started_at=now,
        )
    )

    response = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=12))

    assert response.assigned_counter_id == 2


def test_complete_event_rebuilds_waiting_schedule_from_now(queue_service: QueueService) -> None:
    queue_service.repository.counters = [queue_service.repository.counters[0]]

    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210", item_count=1))
    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=1))

    first_token = queue_service.repository.tokens[0]
    first_token.status = QueueTokenStatus.SERVING
    first_token.service_started_at = datetime.now(timezone.utc) - timedelta(minutes=20)

    event_time_floor = datetime.now(timezone.utc)
    queue_service.complete_token(first_token.id)

    second_token = queue_service.repository.tokens[1]
    assert second_token.status == QueueTokenStatus.WAITING
    assert second_token.calling_time is not None
    assert second_token.calling_time >= event_time_floor


def test_called_event_rebuilds_waiting_without_additive_drift(queue_service: QueueService) -> None:
    queue_service.repository.counters = [queue_service.repository.counters[0]]

    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210", item_count=1))
    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543211", item_count=1))
    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543212", item_count=1))

    first_token = queue_service.repository.tokens[0]
    first_token.calling_time = datetime.now(timezone.utc) - timedelta(minutes=15)

    response = queue_service.handle_queue_event(
        QueueEventRequest(token_id=first_token.id, event=QueueEventType.CALLED, cancellation_reason=None)
    )

    second_token = queue_service.repository.tokens[1]
    third_token = queue_service.repository.tokens[2]

    assert response.status == QueueTokenStatus.CALLED
    assert second_token.calling_time is not None
    assert third_token.calling_time is not None
    assert second_token.calling_time >= response.called_at
    assert third_token.calling_time > second_token.calling_time


def test_called_event_rejects_already_called_token(queue_service: QueueService) -> None:
    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543210", item_count=1))
    token = queue_service.repository.tokens[0]

    queue_service.handle_queue_event(QueueEventRequest(token_id=token.id, event=QueueEventType.CALLED))

    with pytest.raises(HTTPException) as exc_info:
        queue_service.handle_queue_event(QueueEventRequest(token_id=token.id, event=QueueEventType.CALLED))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Only waiting token can be called"


def test_complete_event_moves_waiting_earlier_when_served_faster(queue_service: QueueService) -> None:
    queue_service.repository.counters = [queue_service.repository.counters[0]]

    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543300", item_count=20))
    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543301", item_count=1))

    first_token = queue_service.repository.tokens[0]
    second_token = queue_service.repository.tokens[1]

    old_second_calling_time = second_token.calling_time
    first_token.status = QueueTokenStatus.SERVING
    first_token.service_started_at = datetime.now(timezone.utc) - timedelta(minutes=2)

    queue_service.complete_token(first_token.id)

    assert old_second_calling_time is not None
    assert second_token.calling_time is not None
    assert second_token.calling_time < old_second_calling_time


def test_complete_event_moves_waiting_later_when_served_slower(queue_service: QueueService) -> None:
    queue_service.repository.counters = [queue_service.repository.counters[0]]

    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543400", item_count=1))
    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543401", item_count=1))

    first_token = queue_service.repository.tokens[0]
    second_token = queue_service.repository.tokens[1]

    # Simulate stale optimistic schedule that expected second token earlier than current event time.
    second_token.calling_time = datetime.now(timezone.utc) - timedelta(minutes=3)
    old_second_calling_time = second_token.calling_time

    first_token.status = QueueTokenStatus.SERVING
    first_token.service_started_at = datetime.now(timezone.utc) - timedelta(minutes=25)

    queue_service.complete_token(first_token.id)

    assert old_second_calling_time is not None
    assert second_token.calling_time is not None
    assert second_token.calling_time > old_second_calling_time


def test_customer_cancel_allows_waiting_and_called_tokens(queue_service: QueueService) -> None:
    queue_service.repository.counters = [queue_service.repository.counters[0]]
    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543500", item_count=1))
    called = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543501", item_count=1))
    queue_service.handle_queue_event(QueueEventRequest(token_id=called.token_id, event=QueueEventType.CALLED))

    waiting_response = queue_service.cancel_token_by_customer(1)
    called_response = queue_service.cancel_token_by_customer(called.token_id)

    assert waiting_response.status == QueueTokenStatus.CANCELLED
    assert called_response.status == QueueTokenStatus.CANCELLED
    assert queue_service.repository.tokens[0].cancellation_reason == "Cancelled by customer"
    assert queue_service.repository.tokens[1].cancellation_reason == "Cancelled by customer"


def test_customer_cancel_rejects_serving_and_terminal_tokens(queue_service: QueueService) -> None:
    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543600", item_count=1))
    token = queue_service.repository.tokens[0]
    token.status = QueueTokenStatus.SERVING

    with pytest.raises(HTTPException) as serving_exc:
        queue_service.cancel_token_by_customer(token.id)

    token.status = QueueTokenStatus.COMPLETED

    with pytest.raises(HTTPException) as terminal_exc:
        queue_service.cancel_token_by_customer(token.id)

    assert serving_exc.value.status_code == 409
    assert terminal_exc.value.status_code == 409


def test_customer_move_last_cancels_original_and_creates_replacement_in_same_counter(queue_service: QueueService) -> None:
    queue_service.repository.counters = [queue_service.repository.counters[0]]
    first = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543700", item_count=1))
    second = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543701", item_count=3))
    second_token = queue_service.repository.get_token(second.token_id)
    old_second_calling_time = second_token.calling_time

    replacement = queue_service.move_token_last_by_customer(first.token_id)
    original = queue_service.repository.get_token(first.token_id)
    replacement_token = queue_service.repository.get_token(replacement.token_id)

    assert original.status == QueueTokenStatus.CANCELLED
    assert original.cancellation_reason == "Moved to end by customer"
    assert replacement.status == QueueTokenStatus.WAITING
    assert replacement.assigned_counter_id == original.assigned_counter_id
    assert replacement.phone_number == original.phone_number
    assert replacement.item_count == original.item_count
    assert replacement.token_id != original.id
    assert replacement_token.calling_time > second_token.calling_time
    assert second_token.calling_time <= old_second_calling_time
    assert queue_service.repository.counters[0].next_available_time > replacement_token.calling_time


def test_shared_queue_customer_move_last_keeps_replacement_unassigned(queue_service: QueueService) -> None:
    queue_service.repository.counters = [queue_service.repository.counters[0]]
    queue_service.repository.store_configs[1] = make_store_config("BILL", shared_queue_enabled=True)
    first = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543700", item_count=1))
    second = queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543701", item_count=1))
    second_token = queue_service.repository.get_token(second.token_id)

    replacement = queue_service.move_token_last_by_customer(first.token_id)
    original = queue_service.repository.get_token(first.token_id)
    replacement_token = queue_service.repository.get_token(replacement.token_id)

    assert original.status == QueueTokenStatus.CANCELLED
    assert original.cancellation_reason == "Moved to end by customer"
    assert replacement.status == QueueTokenStatus.WAITING
    assert replacement.assigned_counter_id is None
    assert replacement.token_number == "BILL-Q-003"
    assert replacement_token.calling_time > second_token.calling_time


def test_customer_move_last_rejects_serving_terminal_missing_and_unassigned_tokens(queue_service: QueueService) -> None:
    queue_service.join_queue(QueueJoinRequest(store_id=1, section_id=1, phone_number="9876543800", item_count=1))
    token = queue_service.repository.tokens[0]
    token.status = QueueTokenStatus.SERVING

    with pytest.raises(HTTPException) as serving_exc:
        queue_service.move_token_last_by_customer(token.id)

    token.status = QueueTokenStatus.CANCELLED

    with pytest.raises(HTTPException) as terminal_exc:
        queue_service.move_token_last_by_customer(token.id)

    unassigned = QueueToken(
        id=99,
        store_id=1,
        section_id=1,
        assigned_counter_id=None,
        token_number="UNASSIGNED",
        phone_number="9876543899",
        status=QueueTokenStatus.WAITING,
        calling_time=datetime.now(timezone.utc),
    )
    queue_service.repository.tokens.append(unassigned)

    with pytest.raises(HTTPException) as unassigned_exc:
        queue_service.move_token_last_by_customer(unassigned.id)

    with pytest.raises(HTTPException) as missing_exc:
        queue_service.move_token_last_by_customer(404)

    assert serving_exc.value.status_code == 409
    assert terminal_exc.value.status_code == 409
    assert unassigned_exc.value.status_code == 409
    assert missing_exc.value.status_code == 404
