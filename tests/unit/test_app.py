import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import Settings
from app.main import create_app


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


def test_create_app_uses_given_settings(app: FastAPI, settings: Settings) -> None:
    assert app.title == settings.app_name
    assert app.state.settings is settings


def test_lifespan_creates_engine(app: FastAPI, settings: Settings) -> None:
    with TestClient(app):
        engine: AsyncEngine = app.state.engine
        assert engine.url.render_as_string(hide_password=False) == str(settings.database_url)
        assert app.state.session_factory.kw["bind"] is engine


def test_health_returns_app_status(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {}}
