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
def auth(client: TestClient) -> dict[str, str]:
    email = f"perfil-{uuid4().hex[:8]}@example.com"
    client.post("/auth/register", json={"email": email, "password": PASSWORD, "name": "Ana"})
    login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_me_returns_profile_with_mep_by_default(client: TestClient, auth: dict[str, str]) -> None:
    response = client.get("/me", headers=auth)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "email", "name", "preferences"}
    assert body["name"] == "Ana"
    assert body["preferences"] == {"default_rate_type": "MEP"}


def test_patch_preferences_changes_the_rate(client: TestClient, auth: dict[str, str]) -> None:
    updated = client.patch("/me/preferences", headers=auth, json={"default_rate_type": "BLUE"})
    invalid = client.patch("/me/preferences", headers=auth, json={"default_rate_type": "TARJETA"})

    assert updated.status_code == 200
    assert client.get("/me", headers=auth).json()["preferences"]["default_rate_type"] == "BLUE"
    assert invalid.status_code == 422


def test_me_requires_a_token(client: TestClient) -> None:
    assert client.get("/me").status_code == 401
    assert client.patch("/me/preferences", json={"default_rate_type": "CCL"}).status_code == 401
