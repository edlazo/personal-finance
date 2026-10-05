from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_create_app_uses_given_settings(settings: Settings) -> None:
    app = create_app(settings)

    assert app.title == settings.app_name
    assert app.state.settings is settings


def test_health_returns_app_status(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {}}
