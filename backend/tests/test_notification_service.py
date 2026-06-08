from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.counter import Counter, CounterType
from app.models.notification import (
    DEFAULT_CALLED_TEMPLATE,
    DEFAULT_NEXT_SOON_TEMPLATE,
    NotificationModuleType,
    NotificationStatus,
    NotificationType,
    StoreNotificationConfig,
)
from app.models.queue_token import QueueToken, QueueTokenStatus
from app.models.store import Store
from app.models.trial_queue_token import TrialQueueToken, TrialQueueTokenStatus
from app.models.trial_studio import TrialStudio, TrialStudioType
from app.schemas.notification import StoreNotificationConfigUpdateRequest
from app.services.notification_service import NotificationService
from app.services.sms_client import MockSmsClient


class FakeNotificationRepository:
    def __init__(self, db: object) -> None:
        now = datetime.now(timezone.utc)
        self.stores = {1: Store(id=1, store_number="S-001", name="Main Store")}
        self.configs = {
            1: StoreNotificationConfig(
                id=1,
                store_id=1,
                is_enabled=True,
                notify_on_called=True,
                notify_on_next_soon=True,
                next_soon_token_ahead_count=2,
                called_message_template=DEFAULT_CALLED_TEMPLATE,
                next_soon_message_template=DEFAULT_NEXT_SOON_TEMPLATE,
                created_at=now,
                updated_at=now,
            )
        }
        self.logs = []
        self.counters = {1: Counter(id=1, section_id=1, name="Counter 1", counter_type=CounterType.REGULAR, next_available_time=now)}
        self.studios = {1: TrialStudio(id=1, trial_zone_id=1, name="Studio 1", studio_type=TrialStudioType.REGULAR, next_available_time=now)}
        self.checkout_tokens = [
            QueueToken(id=1, store_id=1, assigned_counter_id=1, token_number="C-001", phone_number="9000000001", status=QueueTokenStatus.WAITING, calling_time=now),
            QueueToken(id=2, store_id=1, assigned_counter_id=1, token_number="C-002", phone_number="9000000002", status=QueueTokenStatus.WAITING, calling_time=now),
            QueueToken(id=3, store_id=1, assigned_counter_id=1, token_number="C-003", phone_number="9000000003", status=QueueTokenStatus.WAITING, calling_time=now),
        ]
        self.trial_tokens = [
            TrialQueueToken(id=1, store_id=1, assigned_studio_id=1, token_number="T-001", phone_number="9000000004", status=TrialQueueTokenStatus.WAITING, calling_time=now),
            TrialQueueToken(id=2, store_id=1, assigned_studio_id=1, token_number="T-002", phone_number="9000000005", status=TrialQueueTokenStatus.WAITING, calling_time=now),
        ]
        self.next_id = 1
        self.committed = False

    def get_store(self, store_id):
        return self.stores.get(store_id)

    def get_config(self, store_id):
        return self.configs.get(store_id)

    def create_config(self, config):
        config.id = config.id or self.next_id
        self.next_id += 1
        self.configs[config.store_id] = config
        return config

    def notification_exists(self, module_type, token_id, notification_type):
        return any(log.module_type == module_type and log.token_id == token_id and log.notification_type == notification_type for log in self.logs)

    def create_log(self, log):
        log.id = self.next_id
        self.next_id += 1
        log.created_at = datetime.now(timezone.utc)
        log.updated_at = log.created_at
        self.logs.append(log)
        return log

    def list_logs(self, store_id, limit):
        return [log for log in self.logs if log.store_id == store_id][:limit]

    def list_active_checkout_tokens(self):
        return self.checkout_tokens

    def list_active_trial_tokens(self):
        return self.trial_tokens

    def get_counter(self, counter_id):
        return self.counters.get(counter_id)

    def get_studio(self, studio_id):
        return self.studios.get(studio_id)

    def commit(self):
        self.committed = True

    def refresh(self, instance):
        return None


def make_service(monkeypatch, sms_client=None):
    fake_repository = FakeNotificationRepository(None)

    def repository_factory(db):
        return fake_repository

    monkeypatch.setattr("app.services.notification_service.NotificationRepository", repository_factory)
    return NotificationService(None, sms_client=sms_client), fake_repository


def test_checkout_called_notification_creates_sent_log(monkeypatch) -> None:
    service, repository = make_service(monkeypatch)

    log = service.notify_checkout_called(repository.checkout_tokens[0])

    assert log.status == NotificationStatus.SENT
    assert log.module_type == NotificationModuleType.CHECKOUT
    assert log.notification_type == NotificationType.TOKEN_CALLED
    assert "C-001" in log.message


def test_next_soon_scanner_sends_only_second_lane_tokens_and_no_duplicates(monkeypatch) -> None:
    service, repository = make_service(monkeypatch)

    first_count = service.send_next_soon_notifications()
    second_count = service.send_next_soon_notifications()

    assert first_count == 2
    assert second_count == 0
    assert [(log.module_type, log.token_id, log.notification_type) for log in repository.logs] == [
        (NotificationModuleType.CHECKOUT, 2, NotificationType.NEXT_SOON),
        (NotificationModuleType.TRIAL, 2, NotificationType.NEXT_SOON),
    ]


def test_next_soon_scanner_uses_configured_lane_position(monkeypatch) -> None:
    service, repository = make_service(monkeypatch)
    repository.configs[1].next_soon_token_ahead_count = 3
    repository.trial_tokens.append(
        TrialQueueToken(
            id=3,
            store_id=1,
            assigned_studio_id=1,
            token_number="T-003",
            phone_number="9000000006",
            status=TrialQueueTokenStatus.WAITING,
            calling_time=datetime.now(timezone.utc),
        )
    )

    sent_count = service.send_next_soon_notifications()

    assert sent_count == 2
    assert [(log.module_type, log.token_id, log.notification_type) for log in repository.logs] == [
        (NotificationModuleType.CHECKOUT, 3, NotificationType.NEXT_SOON),
        (NotificationModuleType.TRIAL, 3, NotificationType.NEXT_SOON),
    ]


def test_notification_config_rejects_invalid_next_soon_position() -> None:
    with pytest.raises(ValidationError):
        StoreNotificationConfigUpdateRequest(next_soon_token_ahead_count=1)


def test_disabled_config_skips_notification(monkeypatch) -> None:
    service, repository = make_service(monkeypatch)
    repository.configs[1].is_enabled = False

    log = service.notify_checkout_called(repository.checkout_tokens[0])

    assert log.status == NotificationStatus.SKIPPED
    assert log.error_message == "Notifications disabled"


def test_mock_sms_failure_marks_notification_failed(monkeypatch) -> None:
    service, repository = make_service(monkeypatch, sms_client=MockSmsClient(should_fail=True))

    log = service.notify_checkout_called(repository.checkout_tokens[0])

    assert log.status == NotificationStatus.FAILED
    assert log.error_message == "Mock SMS failure"
