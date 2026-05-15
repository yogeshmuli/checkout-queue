from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app


class FakeDbSession:
    def execute(self, statement: object) -> None:
        return None


def override_get_db() -> FakeDbSession:
    return FakeDbSession()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health_check_returns_ok() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "connected"
