from fastapi.testclient import TestClient

from app.api.v1.endpoints import health as health_endpoint


def test_health_check_ok(client: TestClient):
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


def test_health_check_unhealthy_returns_503(client: TestClient, monkeypatch):
    def mock_check_database_health() -> bool:
        raise Exception("database unavailable")

    monkeypatch.setattr(health_endpoint, "check_database_health", mock_check_database_health)

    response = client.get("/api/v1/health/")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "down"}
