import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import Settings
from app.main import create_app
from app.shared.api.health import database_check


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


def override_database_check(app: FastAPI, *, available: bool) -> None:
    async def fake_check() -> bool:
        return available

    app.dependency_overrides[database_check] = fake_check


def test_create_app_uses_given_settings(app: FastAPI, settings: Settings) -> None:
    assert app.title == settings.app_name
    assert app.state.settings is settings


def test_lifespan_creates_engine(app: FastAPI, settings: Settings) -> None:
    with TestClient(app):
        engine: AsyncEngine = app.state.engine
        assert engine.url.render_as_string(hide_password=False) == str(settings.database_url)
        assert app.state.session_factory.kw["bind"] is engine


def test_health_ok_when_database_available(app: FastAPI) -> None:
    override_database_check(app, available=True)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": "ok"}}


def test_health_503_when_database_unavailable(app: FastAPI) -> None:
    override_database_check(app, available=False)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "checks": {"database": "error"}}
