from datetime import datetime

from pydantic import BaseModel, Field

from app.models.checkout_section import CheckoutSectionType


class SectionBase(BaseModel):
    store_id: int
    name: str = Field(min_length=1, max_length=100)
    section_type: CheckoutSectionType
    is_active: bool = True


class SectionCreateRequest(SectionBase):
    pass


class SectionUpdateRequest(BaseModel):
    store_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    section_type: CheckoutSectionType | None = None
    is_active: bool | None = None


class SectionResponse(BaseModel):
    id: int
    store_id: int
    name: str
    section_type: CheckoutSectionType
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
