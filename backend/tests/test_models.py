import app.models  # noqa: F401
from app.core.database import Base
from app.models.checkout_section import CheckoutSectionType
from app.schemas.section import SectionCreateRequest


def test_core_checkout_tables_are_registered() -> None:
    expected_tables = {
        "stores",
        "store_calendar_days",
        "store_calendar_events",
        "store_configs",
        "store_holidays",
        "checkout_sections",
        "counters",
        "queue_tokens",
        "users",
        "user_store_access",
        "refresh_tokens",
        "ml_model_metadata",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())


def test_section_schema_accepts_current_frontend_section_types() -> None:
    for section_type in (CheckoutSectionType.CSD, CheckoutSectionType.RETURNS, CheckoutSectionType.EXCHANGE):
        payload = SectionCreateRequest(store_id=1, name=f"{section_type.value} section", section_type=section_type)

        assert payload.section_type == section_type
