"""Boot smoke test: the application starts and answers the health check."""

from app.main import app
from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_application_uses_fridge_pal_title() -> None:
    assert app.title == "Fridge Pal"
