from collections import defaultdict
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notification import (
    DEFAULT_CALLED_TEMPLATE,
    DEFAULT_NEXT_SOON_TEMPLATE,
    NotificationChannel,
    NotificationLog,
    NotificationModuleType,
    NotificationStatus,
    NotificationType,
    StoreNotificationConfig,
)
from app.models.queue_token import QueueToken
from app.models.trial_queue_token import TrialQueueToken
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import StoreNotificationConfigUpdateRequest
from app.services.sms_client import MockSmsClient


class NotificationService:
    def __init__(self, db: Session, sms_client: MockSmsClient | None = None) -> None:
        self.repository = NotificationRepository(db)
        self.sms_client = sms_client or MockSmsClient(should_fail=settings.MOCK_SMS_SHOULD_FAIL)

    def get_config(self, store_id: int) -> StoreNotificationConfig:
        self._ensure_store_exists(store_id)
        config = self.repository.get_config(store_id)
        if config is not None:
            return config
        config = StoreNotificationConfig(store_id=store_id)
        self.repository.create_config(config)
        self.repository.commit()
        self.repository.refresh(config)
        return config

    def update_config(self, store_id: int, payload: StoreNotificationConfigUpdateRequest) -> StoreNotificationConfig:
        self._ensure_store_exists(store_id)
        config = self.repository.get_config(store_id)
        if config is None:
            config = StoreNotificationConfig(store_id=store_id)
            self.repository.create_config(config)

        for field, value in payload.model_dump().items():
            setattr(config, field, value)

        self.repository.commit()
        self.repository.refresh(config)
        return config

    def list_logs(self, store_id: int, limit: int = 50) -> list[NotificationLog]:
        self._ensure_store_exists(store_id)
        return self.repository.list_logs(store_id, max(1, min(limit, 200)))

    def notify_checkout_called(self, token: QueueToken) -> NotificationLog | None:
        return self._send_for_token(
            module_type=NotificationModuleType.CHECKOUT,
            token=token,
            notification_type=NotificationType.TOKEN_CALLED,
            service_point_name=self._checkout_service_point_name(token),
        )

    def notify_trial_called(self, token: TrialQueueToken) -> NotificationLog | None:
        return self._send_for_token(
            module_type=NotificationModuleType.TRIAL,
            token=token,
            notification_type=NotificationType.TOKEN_CALLED,
            service_point_name=self._trial_service_point_name(token),
        )

    def send_next_soon_notifications(self) -> int:
        sent_count = 0
        for token in self._checkout_next_soon_tokens():
            if self._send_for_token(
                module_type=NotificationModuleType.CHECKOUT,
                token=token,
                notification_type=NotificationType.NEXT_SOON,
                service_point_name=self._checkout_service_point_name(token),
            ):
                sent_count += 1

        for token in self._trial_next_soon_tokens():
            if self._send_for_token(
                module_type=NotificationModuleType.TRIAL,
                token=token,
                notification_type=NotificationType.NEXT_SOON,
                service_point_name=self._trial_service_point_name(token),
            ):
                sent_count += 1
        return sent_count

    def _send_for_token(
        self,
        module_type: NotificationModuleType,
        token: QueueToken | TrialQueueToken,
        notification_type: NotificationType,
        service_point_name: str,
    ) -> NotificationLog | None:
        if self.repository.notification_exists(module_type, token.id, notification_type):
            return None

        config = self.repository.get_config(token.store_id)
        if config is None or not config.is_enabled:
            return self._create_log(module_type, token, notification_type, NotificationStatus.SKIPPED, "", "Notifications disabled")

        if notification_type == NotificationType.TOKEN_CALLED and not config.notify_on_called:
            return self._create_log(module_type, token, notification_type, NotificationStatus.SKIPPED, "", "Called notifications disabled")
        if notification_type == NotificationType.NEXT_SOON and not config.notify_on_next_soon:
            return self._create_log(module_type, token, notification_type, NotificationStatus.SKIPPED, "", "Next-soon notifications disabled")

        message = self._render_message(config, token, notification_type, module_type, service_point_name)
        log = self._create_log(module_type, token, notification_type, NotificationStatus.PENDING, message, None)
        try:
            self.sms_client.send_sms(token.phone_number, message)
        except Exception as exc:
            log.status = NotificationStatus.FAILED
            log.error_message = str(exc)
        else:
            log.status = NotificationStatus.SENT
            log.sent_at = datetime.now(timezone.utc)
        self.repository.commit()
        self.repository.refresh(log)
        return log

    def _create_log(
        self,
        module_type: NotificationModuleType,
        token: QueueToken | TrialQueueToken,
        notification_type: NotificationType,
        log_status: NotificationStatus,
        message: str,
        error_message: str | None,
    ) -> NotificationLog:
        log = NotificationLog(
            store_id=token.store_id,
            module_type=module_type,
            token_id=token.id,
            phone_number=token.phone_number,
            notification_type=notification_type,
            channel=NotificationChannel.SMS,
            status=log_status,
            message=message,
            error_message=error_message,
            sent_at=datetime.now(timezone.utc) if log_status == NotificationStatus.SENT else None,
        )
        self.repository.create_log(log)
        self.repository.commit()
        self.repository.refresh(log)
        return log

    def _render_message(
        self,
        config: StoreNotificationConfig,
        token: QueueToken | TrialQueueToken,
        notification_type: NotificationType,
        module_type: NotificationModuleType,
        service_point_name: str,
    ) -> str:
        template = (
            config.called_message_template or DEFAULT_CALLED_TEMPLATE
            if notification_type == NotificationType.TOKEN_CALLED
            else config.next_soon_message_template or DEFAULT_NEXT_SOON_TEMPLATE
        )
        store = self.repository.get_store(token.store_id)
        values = {
            "token_number": token.token_number,
            "store_name": store.name if store else f"Store #{token.store_id}",
            "service_point_name": service_point_name,
            "module_name": "Checkout Queue" if module_type == NotificationModuleType.CHECKOUT else "Trial Queue",
        }
        return template.format_map(defaultdict(str, values))

    def _checkout_next_soon_tokens(self) -> list[QueueToken]:
        grouped: dict[int, list[QueueToken]] = defaultdict(list)
        for token in self.repository.list_active_checkout_tokens():
            if token.assigned_counter_id is not None:
                grouped[token.assigned_counter_id].append(token)
        return [tokens[1] for tokens in grouped.values() if len(tokens) >= 2]

    def _trial_next_soon_tokens(self) -> list[TrialQueueToken]:
        grouped: dict[int, list[TrialQueueToken]] = defaultdict(list)
        for token in self.repository.list_active_trial_tokens():
            if token.assigned_studio_id is not None:
                grouped[token.assigned_studio_id].append(token)
        return [tokens[1] for tokens in grouped.values() if len(tokens) >= 2]

    def _checkout_service_point_name(self, token: QueueToken) -> str:
        if token.assigned_counter_id is None:
            return "the checkout counter"
        counter = self.repository.get_counter(token.assigned_counter_id)
        return counter.name or f"Counter #{counter.id}" if counter else "the checkout counter"

    def _trial_service_point_name(self, token: TrialQueueToken) -> str:
        if token.assigned_studio_id is None:
            return "the studio"
        studio = self.repository.get_studio(token.assigned_studio_id)
        return studio.name or f"Studio #{studio.id}" if studio else "the studio"

    def _ensure_store_exists(self, store_id: int) -> None:
        if self.repository.get_store(store_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
