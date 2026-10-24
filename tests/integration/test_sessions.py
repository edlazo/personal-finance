from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import PostgresDsn

from app.config import Settings
from app.main import create_app

pytestmark = pytest.mark.integration

PASSWORD = "clave-larga-123"


@pytest.fixture
def client(migrated_database_url: str) -> Iterator[TestClient]:
    settings = Settings(
        _env_file=None, environment="test", database_url=PostgresDsn(migrated_database_url)
    )
    with TestClient(create_app(settings)) as client:
        yield client


@pytest.fixture
def refresh_token(client: TestClient) -> str:
    email = f"sesion-{uuid4().hex[:8]}@example.com"
    client.post("/auth/register", json={"email": email, "password": PASSWORD, "name": "Ana"})
    login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    return str(login.json()["refresh_token"])


def test_refresh_rotates_and_the_old_token_stops_working(
    client: TestClient, refresh_token: str
) -> None:
    rotated = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    reused = client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != refresh_token
    assert reused.status_code == 401
    assert reused.headers["www-authenticate"] == "Bearer"


def test_logout_revokes_the_refresh_token(client: TestClient, refresh_token: str) -> None:
    first = client.post("/auth/logout", json={"refresh_token": refresh_token})
    again = client.post("/auth/logout", json={"refresh_token": refresh_token})
    after = client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert first.status_code == 204
    assert again.status_code == 204
    assert after.status_code == 401
