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
        self.calendar_days: dict[int, list[StoreCalendarDay]] = {}
        self.holidays: dict[tuple[int, object], StoreHoliday] = {}
        now = datetime.now(timezone.utc)
        self.counters = [
            Counter(id=1, section_id=1, counter_type="regular", name="C1", is_active=True, next_available_time=now),
            Counter(id=2, section_id=1, counter_type="regular", name="C2", is_active=True, next_available_time=now),
        ]

    def get_store(self, store_id: int) -> Store | None:
        return self.stores.get(store_id)

    def get_store_config(self, store_id: int) -> StoreConfig | None:
        return self.store_configs.get(store_id)

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

    def count_tokens_for_numbering(self, store_id: int, section_id: int | None) -> int:
        return len([token for token in self.tokens if token.store_id == store_id and token.section_id == section_id])

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
    assert response.token_number == "S1-001"
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
    assert response.token_number == "BILL-001"
    assert token.service_time_minutes == 8


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
