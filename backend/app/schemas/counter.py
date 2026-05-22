from datetime import datetime

from pydantic import BaseModel, Field


class CounterBase(BaseModel):
    section_id: int
    counter_type: str = Field(min_length=1, max_length=50)
    name: str | None = Field(default=None, max_length=100)
    is_active: bool = True


class CounterCreateRequest(CounterBase):
    pass


class CounterUpdateRequest(BaseModel):
    section_id: int | None = None
    counter_type: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


class CounterResponse(BaseModel):
    id: int
    section_id: int
    counter_type: str
    name: str | None
    is_active: bool
    next_available_time: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}