from datetime import datetime

from pydantic import BaseModel, Field

from app.models.trial_zone import TrialZoneGender, TrialZoneType


class TrialZoneCreateRequest(BaseModel):
    store_id: int
    name: str = Field(min_length=1, max_length=100)
    zone_type: TrialZoneType = TrialZoneType.REGULAR
    gender: TrialZoneGender = TrialZoneGender.UNISEX
    is_active: bool = True


class TrialZoneUpdateRequest(BaseModel):
    store_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    zone_type: TrialZoneType | None = None
    gender: TrialZoneGender | None = None
    is_active: bool | None = None


class TrialZoneResponse(BaseModel):
    id: int
    store_id: int
    name: str
    zone_type: TrialZoneType
    gender: TrialZoneGender
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
