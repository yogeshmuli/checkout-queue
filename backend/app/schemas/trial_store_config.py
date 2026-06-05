from datetime import datetime

from pydantic import BaseModel, Field


class TrialStoreConfigUpdateRequest(BaseModel):
    token_id_prefix: str | None = Field(default=None, min_length=1, max_length=20)
    base_service_minutes: int = Field(default=8, ge=0, le=240)
    per_unit_service_minutes: float = Field(default=1.0, ge=0, le=60)
    min_service_minutes: int = Field(default=10, ge=1, le=240)


class TrialStoreConfigResponse(BaseModel):
    id: int
    store_id: int
    token_id_prefix: str | None
    base_service_minutes: int
    per_unit_service_minutes: float
    min_service_minutes: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
