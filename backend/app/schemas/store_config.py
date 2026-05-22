from datetime import datetime

from pydantic import BaseModel, Field


class StoreConfigBase(BaseModel):
    token_id_prefix: str | None = Field(default=None, min_length=1, max_length=20)
    base_service_minutes: int = Field(default=4, ge=0, le=240)
    per_item_service_minutes: float = Field(default=0.25, ge=0, le=60)
    min_service_minutes: int = Field(default=5, ge=1, le=240)


class StoreConfigUpdateRequest(StoreConfigBase):
    pass


class StoreConfigResponse(StoreConfigBase):
    id: int
    store_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
