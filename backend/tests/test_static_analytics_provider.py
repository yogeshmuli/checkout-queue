from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.services.analytics_service import AnalyticsService
from app.services.static_analytics_provider import StaticAnalyticsProvider, load_static_analytics_data
from app.services.trial_analytics_service import TrialAnalyticsService


class StaticOnlyRepository:
    def __init__(self, store):
        self.store = store
        self.metadata_calls = 0

    def get_store(self, store_id):
        return self.store

    def get_latest_model_metadata(self, store_id):
        self.metadata_calls += 1
        return None

    def __getattr__(self, name):
        raise AssertionError(f"Static history must not query {name}")


class EmptyRealRepository:
    def __init__(self, store):
        self.store = store

    def get_store(self, store_id): return self.store
    def get_latest_model_metadata(self, store_id): return None
    def list_sections(self, store_id): return []
    def list_counters(self, store_id): return []
    def list_zones(self, store_id): return []
    def list_studios(self, store_id): return []
    def list_active_tokens(self, store_id): return []
    def list_tokens_since(self, store_id, start_at): return []
    def list_calendar_events(self, store_id, start_date, end_date): return []


def service_with(service_type, repository):
    service = service_type.__new__(service_type)
    service.repository = repository
    return service


def test_static_fixture_preserves_workbook_values_and_shifts_dates():
    fixture = load_static_analytics_data()
    daily_rows = fixture["date_based_analytics"]
    assert len(daily_rows) == 90
    assert daily_rows[0] == {"source_date": "01-10-2024", "is_promotion_day": False, "footfall": 246, "check_ins": 177, "completed": 136, "cancellations": 40, "avg_wait_minutes": 5.3, "avg_service_minutes": 4.3, "avg_items": 2.7}
    assert daily_rows[-1]["source_date"] == "29-12-2024"
    assert daily_rows[-1]["completed"] == 249
    store = SimpleNamespace(id=9, store_number="S-9", name="Static Store")
    now = datetime(2026, 8, 3, 12, tzinfo=timezone.utc)

    response = StaticAnalyticsProvider().trial(store, 7, None, now)

    assert len(response.daily_trends) == 7
    assert response.daily_trends[0].day.isoformat() == "2026-07-28"
    assert response.daily_trends[-1].day.isoformat() == "2026-08-03"
    assert response.daily_trends[-1].completed_count == 249
    assert [(row.avg_footfall, row.avg_wait_time, row.avg_items) for row in StaticAnalyticsProvider().trial(store, 90, None, now).promotion_stats] == [(310.7, 6.3, 2.7), (496.0, 11.8, 6.7)]
    assert [row.zone_name for row in response.zone_stats] == ["Men's Trial", "Women's Trial 1", "Women's Trial 2", "Unisex Trial"]
    assert response.zone_stats[0].total_trials == 6425


def test_weekly_charts_read_named_json_rows_directly():
    store = SimpleNamespace(id=9, store_number="S-9", name="Static Store")
    provider = StaticAnalyticsProvider()
    provider.data["segmented_analysis"]["weekly_patterns"][0]["avg_visits"] = 999

    response = provider.checkout(store, 7, None, datetime(2026, 8, 3, tzinfo=timezone.utc))

    assert response.weekly_stats[0].day_name == "Monday"
    assert response.weekly_stats[0].total_visits == 999


def test_checkout_static_fixture_uses_generic_sections_and_real_store_identity():
    store = SimpleNamespace(id=21, store_number="REAL-21", name="Real Store")

    response = StaticAnalyticsProvider().checkout(store, 30, None, datetime(2026, 8, 3, tzinfo=timezone.utc))

    assert response.store.id == 21
    assert [row.section_name for row in response.sections] == ["Section 1", "Section 2", "Section 3", "Section 4"]
    assert [row.counter_name for row in response.counters] == ["Counter 1", "Counter 2", "Counter 3", "Counter 4"]
    assert len(response.daily_trends) == 30


def test_services_switch_independently_and_skip_historical_queries(monkeypatch):
    store = SimpleNamespace(id=1, store_number="S-1", name="Store")
    checkout_repository = StaticOnlyRepository(store)
    trial_repository = StaticOnlyRepository(store)
    monkeypatch.setattr(settings, "CHECKOUT_ANALYTICS_HISTORY_MODE", "static")
    monkeypatch.setattr(settings, "TRIAL_ANALYTICS_HISTORY_MODE", "static")

    checkout = service_with(AnalyticsService, checkout_repository).get_store_analytics(1, 7)
    trial = service_with(TrialAnalyticsService, trial_repository).get_store_analytics(1, 90)

    assert checkout.days == 7
    assert trial.days == 90
    assert checkout_repository.metadata_calls == 1
    assert trial_repository.metadata_calls == 1


def test_history_modes_accept_supported_values_and_reject_invalid_values():
    configured = Settings(
        _env_file=None,
        CHECKOUT_ANALYTICS_HISTORY_MODE="real",
        TRIAL_ANALYTICS_HISTORY_MODE="static",
    )
    assert configured.CHECKOUT_ANALYTICS_HISTORY_MODE == "real"
    assert configured.TRIAL_ANALYTICS_HISTORY_MODE == "static"

    with pytest.raises(ValidationError):
        Settings(_env_file=None, CHECKOUT_ANALYTICS_HISTORY_MODE="invalid")


def test_one_day_live_requests_remain_real_when_static_history_is_enabled(monkeypatch):
    store = SimpleNamespace(id=1, store_number="S-1", name="Store")
    monkeypatch.setattr(settings, "CHECKOUT_ANALYTICS_HISTORY_MODE", "static")
    monkeypatch.setattr(settings, "TRIAL_ANALYTICS_HISTORY_MODE", "static")
    monkeypatch.setattr(StaticAnalyticsProvider, "checkout", lambda *args, **kwargs: pytest.fail("static Checkout provider called"))
    monkeypatch.setattr(StaticAnalyticsProvider, "trial", lambda *args, **kwargs: pytest.fail("static Trial provider called"))

    checkout = service_with(AnalyticsService, EmptyRealRepository(store)).get_store_analytics(1, 1)
    trial = service_with(TrialAnalyticsService, EmptyRealRepository(store)).get_store_analytics(1, 1)

    assert checkout.days == 1
    assert checkout.sections == []
    assert trial.days == 1
    assert trial.zones == []
