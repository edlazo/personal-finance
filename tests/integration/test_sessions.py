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
    """Inicia sesión: el refresh queda en la cookie del cliente y también se devuelve."""
    email = f"sesion-{uuid4().hex[:8]}@example.com"
    client.post("/auth/register", json={"email": email, "password": PASSWORD, "name": "Ana"})
    client.post("/auth/login", json={"email": email, "password": PASSWORD})
    return str(client.cookies["refresh_token"])


def test_refresh_rotates_and_the_old_token_stops_working(
    client: TestClient, refresh_token: str
) -> None:
    rotated = client.post("/auth/refresh")
    # Solo la cookie vieja: sin clear(), httpx2 2.16 manda también la nueva y el server lee esa.
    client.cookies.clear()
    client.cookies.set("refresh_token", refresh_token)
    reused = client.post("/auth/refresh")

    assert rotated.status_code == 200
    assert rotated.cookies["refresh_token"] != refresh_token
    assert reused.status_code == 401
    assert reused.headers["www-authenticate"] == "Bearer"


def test_logout_revokes_the_refresh_token(client: TestClient, refresh_token: str) -> None:
    first = client.post("/auth/logout")
    client.cookies.clear()
    client.cookies.set("refresh_token", refresh_token)
    again = client.post("/auth/logout")
    client.cookies.clear()
    client.cookies.set("refresh_token", refresh_token)
    after = client.post("/auth/refresh")

    assert first.status_code == 204
    assert again.status_code == 204
    assert after.status_code == 401
