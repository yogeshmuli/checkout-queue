from datetime import datetime

from pydantic import BaseModel, Field

from app.models.notification import (
    DEFAULT_CALLED_TEMPLATE,
    DEFAULT_NEXT_SOON_TEMPLATE,
    NotificationChannel,
    NotificationModuleType,
    NotificationStatus,
    NotificationType,
)


class StoreNotificationConfigUpdateRequest(BaseModel):
    is_enabled: bool = False
    notify_on_called: bool = True
    notify_on_next_soon: bool = True
    called_message_template: str = Field(default=DEFAULT_CALLED_TEMPLATE, min_length=1, max_length=500)
    next_soon_message_template: str = Field(default=DEFAULT_NEXT_SOON_TEMPLATE, min_length=1, max_length=500)


class StoreNotificationConfigResponse(StoreNotificationConfigUpdateRequest):
    id: int
    store_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationLogResponse(BaseModel):
    id: int
    store_id: int
    module_type: NotificationModuleType
    token_id: int
    phone_number: str
    notification_type: NotificationType
    channel: NotificationChannel
    status: NotificationStatus
    message: str
    error_message: str | None
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
