from datetime import datetime

from pydantic import BaseModel, Field

from app.models.trial_studio import TrialStudioType


class TrialStudioCreateRequest(BaseModel):
    trial_zone_id: int
    name: str | None = Field(default=None, max_length=100)
    studio_type: TrialStudioType = TrialStudioType.REGULAR
    is_active: bool = True


class TrialStudioUpdateRequest(BaseModel):
    trial_zone_id: int | None = None
    name: str | None = Field(default=None, max_length=100)
    studio_type: TrialStudioType | None = None
    is_active: bool | None = None


class TrialStudioResponse(BaseModel):
    id: int
    trial_zone_id: int
    name: str | None
    studio_type: TrialStudioType
    is_active: bool
    next_available_time: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
