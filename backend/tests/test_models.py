import app.models  # noqa: F401
from app.core.database import Base


def test_core_checkout_tables_are_registered() -> None:
    expected_tables = {
        "stores",
        "store_calendar_days",
        "store_configs",
        "store_holidays",
        "checkout_sections",
        "counters",
        "queue_tokens",
        "users",
        "user_store_access",
        "refresh_tokens",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())
