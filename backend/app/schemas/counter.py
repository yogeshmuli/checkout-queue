from datetime import datetime

from pydantic import BaseModel, Field

from app.models.counter import CounterBasketSizeBand, CounterType


class CounterBase(BaseModel):
    section_id: int
    counter_type: CounterType
    name: str | None = Field(default=None, max_length=100)
    token_prefix: str | None = Field(default=None, max_length=20)
    basket_size_bands: list[CounterBasketSizeBand] | None = None
    is_active: bool = True


class CounterCreateRequest(CounterBase):
    pass


class CounterUpdateRequest(BaseModel):
    section_id: int | None = None
    counter_type: CounterType | None = None
    name: str | None = Field(default=None, max_length=100)
    token_prefix: str | None = Field(default=None, max_length=20)
    basket_size_bands: list[CounterBasketSizeBand] | None = None
    is_active: bool | None = None


class CounterResponse(BaseModel):
    id: int
    section_id: int
    counter_type: CounterType
    name: str | None
    token_prefix: str | None
    basket_size_bands: list[CounterBasketSizeBand] | None
    is_active: bool
    next_available_time: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
