from datetime import datetime

from pydantic import BaseModel, Field


class MLModelMetadataResponse(BaseModel):
    id: int
    store_id: int
    model_type: str
    model_version: str
    status: str
    sample_size: int
    trained_at: datetime | None
    mae: float | None
    r2_score: float | None
    accuracy_score: float | None
    data_quality_score: float | None
    feature_importance: dict[str, float] | None
    error_message: str | None
    training_source: str = "DATABASE"
    original_filename: str | None = None
    source_file_path: str | None = None
    uploaded_by_user_id: int | None = None
    validation_summary: dict[str, int | str] | None = None


class MLTrainingValidationError(BaseModel):
    sheet: str
    row: int | None = None
    column: str | None = None
    message: str


class ServiceTimePredictionRequest(BaseModel):
    section_id: int | None = Field(default=None, gt=0)
    assigned_counter_id: int | None = Field(default=None, gt=0)
    item_count: int | None = Field(default=None, ge=0)
    basket_size: str | None = Field(default=None, max_length=50)
    cart_type: str | None = Field(default=None, max_length=50)
    customer_type: str | None = Field(default=None, max_length=50)
    requested_at: datetime | None = None


class ServiceTimePredictionResponse(BaseModel):
    service_time_minutes: int
    calculation_method: str
    model_version: str | None = None


class TrialServiceTimePredictionRequest(BaseModel):
    trial_zone_id: int | None = Field(default=None, gt=0)
    assigned_studio_id: int | None = Field(default=None, gt=0)
    item_count: int | None = Field(default=None, ge=0)
    customer_type: str | None = Field(default=None, max_length=50)
    requested_at: datetime | None = None
