from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class StoreBase(BaseModel):
    store_number: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    address: str | None = None
    manager_name: str | None = Field(default=None, max_length=150)
    manager_phone: str | None = Field(default=None, min_length=10, max_length=10)
    spoc_name: str | None = Field(default=None, max_length=150)
    spoc_phone: str | None = Field(default=None, min_length=10, max_length=10)
    is_active: bool = True

    @field_validator("manager_phone", "spoc_phone")
    @classmethod
    def validate_phone_number(cls, value: str | None) -> str | None:
        if value is not None and not value.isdigit():
            raise ValueError("Phone number must contain only digits")
        return value


class StoreCreateRequest(StoreBase):
    pass


class StoreUpdateRequest(BaseModel):
    store_number: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    address: str | None = None
    manager_name: str | None = Field(default=None, max_length=150)
    manager_phone: str | None = Field(default=None, min_length=10, max_length=10)
    spoc_name: str | None = Field(default=None, max_length=150)
    spoc_phone: str | None = Field(default=None, min_length=10, max_length=10)
    is_active: bool | None = None

    @field_validator("manager_phone", "spoc_phone")
    @classmethod
    def validate_phone_number(cls, value: str | None) -> str | None:
        if value is not None and not value.isdigit():
            raise ValueError("Phone number must contain only digits")
        return value


class StoreResponse(BaseModel):
    id: int
    store_number: str
    name: str
    address: str | None
    manager_name: str | None
    manager_phone: str | None
    spoc_name: str | None
    spoc_phone: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

