from collections.abc import Iterator
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import PostgresDsn

from app.config import Settings
from app.main import create_app

pytestmark = pytest.mark.integration

PASSWORD = "clave-larga-123"


@pytest.fixture
def settings(migrated_database_url: str) -> Settings:
    return Settings(
        _env_file=None, environment="test", database_url=PostgresDsn(migrated_database_url)
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as client:
        yield client


@pytest.fixture
def registered(client: TestClient) -> dict[str, str]:
    email = f"login-{uuid4().hex[:8]}@example.com"
    response = client.post(
        "/auth/register", json={"email": email, "password": PASSWORD, "name": "Ana"}
    )
    assert response.status_code == 201
    return {"id": response.json()["id"], "email": email}


def test_login_returns_access_and_refresh_tokens(
    client: TestClient, settings: Settings, registered: dict[str, str]
) -> None:
    response = client.post(
        "/auth/login", json={"email": registered["email"].upper(), "password": PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900
    secret = settings.jwt_secret.get_secret_value()
    claims = jwt.decode(body["access_token"], secret, algorithms=["HS256"])
    assert claims["sub"] == registered["id"]


def test_login_fails_with_the_same_message_for_wrong_password_or_email(
    client: TestClient, registered: dict[str, str]
) -> None:
    wrong_password = client.post(
        "/auth/login", json={"email": registered["email"], "password": "otra-clave-456"}
    )
    unknown_email = client.post(
        "/auth/login", json={"email": "nadie@example.com", "password": PASSWORD}
    )

    for response in (wrong_password, unknown_email):
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
    assert wrong_password.json()["detail"] == unknown_email.json()["detail"]
