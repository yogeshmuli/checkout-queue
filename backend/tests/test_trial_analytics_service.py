from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.trial_queue_token import TrialQueueTokenStatus
from app.core.config import settings
from app.services.trial_analytics_service import TrialAnalyticsService


@pytest.fixture(autouse=True)
def use_real_trial_history(monkeypatch):
    monkeypatch.setattr(settings, "TRIAL_ANALYTICS_HISTORY_MODE", "real")


class FakeTrialAnalyticsRepository:
    def __init__(self, store=None, *, zones=None, studios=None, active=None, tokens=None, events=None, metadata=None):
        self.store = store
        self.zones = zones or []
        self.studios = studios or []
        self.active = active or []
        self.tokens = tokens or []
        self.events = events or []
        self.metadata = metadata

    def get_store(self, store_id): return self.store
    def list_zones(self, store_id): return self.zones
    def list_studios(self, store_id): return self.studios
    def list_active_tokens(self, store_id): return self.active
    def list_tokens_since(self, store_id, start_at): return self.tokens
    def list_calendar_events(self, store_id, start_date, end_date): return self.events
    def get_latest_model_metadata(self, store_id): return self.metadata


def token(token_id, status, *, zone_id=10, studio_id=None, item_count=2, created_at=None):
    created_at = created_at or datetime.now(timezone.utc) - timedelta(minutes=10)
    completed_at = created_at + timedelta(minutes=20) if status == TrialQueueTokenStatus.COMPLETED else None
    cancelled_at = created_at + timedelta(minutes=5) if status == TrialQueueTokenStatus.CANCELLED else None
    return SimpleNamespace(
        id=token_id, token_number=f"T-{token_id}", status=status, trial_zone_id=zone_id,
        assigned_studio_id=studio_id, item_count=item_count, customer_type="regular",
        created_at=created_at, updated_at=cancelled_at or completed_at or created_at,
        calling_time=created_at + timedelta(minutes=2), service_started_at=created_at + timedelta(minutes=5) if completed_at else None,
        completed_at=completed_at, cancelled_at=cancelled_at, service_time_minutes=15,
    )


def service_with(repository):
    service = TrialAnalyticsService.__new__(TrialAnalyticsService)
    service.repository = repository
    return service


def test_trial_analytics_builds_live_history_and_empty_ml_summary():
    store = SimpleNamespace(id=1, store_number="S-1", name="Store")
    zone = SimpleNamespace(id=10, name="Menswear", zone_type="REGULAR", gender="MALE")
    studio = SimpleNamespace(id=20, trial_zone_id=10, name="Studio A", studio_type="REGULAR", is_active=True)
    waiting = token(1, TrialQueueTokenStatus.WAITING)
    serving = token(2, TrialQueueTokenStatus.SERVING, studio_id=20)
    completed = token(3, TrialQueueTokenStatus.COMPLETED, studio_id=20)
    cancelled = token(4, TrialQueueTokenStatus.CANCELLED)
    repository = FakeTrialAnalyticsRepository(store, zones=[zone], studios=[studio], active=[waiting, serving], tokens=[waiting, serving, completed, cancelled])

    response = service_with(repository).get_store_analytics(1, 7)

    assert response.metrics.waiting_tokens == 1
    assert response.metrics.serving_tokens == 1
    assert response.metrics.active_studios == 1
    assert response.zones[0].active_studio_sessions[0].assigned_token_number == "T-2"
    assert sum(row.completed_count for row in response.daily_trends) == 1
    assert response.customer_type_stats[0].count == 4
    assert response.item_bucket_stats[0].count == 4
    assert response.ml_summary.status == "NOT_TRAINED"


def test_trial_analytics_returns_empty_groups_and_clamps_days():
    store = SimpleNamespace(id=1, store_number="S-1", name="Store")
    response = service_with(FakeTrialAnalyticsRepository(store)).get_store_analytics(1, 999)

    assert response.days == 90
    assert len(response.daily_trends) == 90
    assert response.metrics.total_studios == 0
    assert response.zones == []


def test_trial_analytics_rejects_unknown_store():
    with pytest.raises(HTTPException) as error:
        service_with(FakeTrialAnalyticsRepository()).get_store_analytics(404, 7)

    assert error.value.status_code == 404
