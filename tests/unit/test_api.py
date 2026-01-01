from fastapi.testclient import TestClient
from src.api.main import app


def test_root():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Self-Healing Pipeline Platform API"
        assert data["status"] == "ok"


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"


def test_list_pipelines():
    with TestClient(app) as client:
        response = client.get("/api/v1/pipelines")
        assert response.status_code == 200
        data = response.json()
        assert "pipelines" in data
        assert "count" in data
        assert data["count"] == 0
