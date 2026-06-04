from pydantic import BaseModel


class DemoToolIds(BaseModel):
    store_id: int | None = None
    checkout_section_id: int | None = None
    checkout_counter_ids: list[int] = []
    trial_zone_id: int | None = None
    trial_studio_ids: list[int] = []


class DemoToolCounts(BaseModel):
    checkout_completed_tokens: int = 0
    checkout_terminal_tokens: int = 0
    checkout_waiting_tokens: int = 0
    trial_completed_tokens: int = 0
    trial_terminal_tokens: int = 0
    trial_waiting_tokens: int = 0
    ml_metadata_rows: int = 0


class DemoTrainingDataResponse(BaseModel):
    exists: bool
    store_number: str
    ids: DemoToolIds
    counts: DemoToolCounts
    checkout_artifact_present: bool = False
    trial_artifact_present: bool = False
    next_steps: list[str] = []
    message: str
