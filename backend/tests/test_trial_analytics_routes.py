from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.routes.trial_analytics_routes import router
from app.services.trial_analytics_service import TrialAnalyticsService


def make_app(role: UserRole | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: None
    if role is not None:
        app.dependency_overrides[get_current_user] = lambda: User(
            id=1, email="admin@example.com", full_name="Admin", password_hash="hash",
            default_role=role, is_active=True,
        )
    return app


def test_trial_analytics_requires_bearer_authentication():
    assert TestClient(make_app()).get("/trial/analytics/stores/1").status_code == 401


def test_trial_analytics_rejects_disallowed_role():
    assert TestClient(make_app(UserRole.CASHIER)).get("/trial/analytics/stores/1").status_code == 403


def test_trial_analytics_validates_days_before_service_call():
    response = TestClient(make_app(UserRole.MANAGER)).get("/trial/analytics/stores/1?days=91")
    assert response.status_code == 422


def test_trial_analytics_propagates_missing_store(monkeypatch):
    def missing(self, store_id, days):
        raise HTTPException(status_code=404, detail="Store not found")

    monkeypatch.setattr(TrialAnalyticsService, "get_store_analytics", missing)
    response = TestClient(make_app(UserRole.STORE_ADMIN)).get("/trial/analytics/stores/404?days=7")
    assert response.status_code == 404
    assert response.json()["detail"] == "Store not found"
