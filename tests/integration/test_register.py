from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import PostgresDsn
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import Settings
from app.main import create_app

pytestmark = pytest.mark.integration


@pytest.fixture
def client(migrated_database_url: str) -> Iterator[TestClient]:
    settings = Settings(
        _env_file=None, environment="test", database_url=PostgresDsn(migrated_database_url)
    )
    with TestClient(create_app(settings)) as client:
        yield client


def new_email() -> str:
    # La base se comparte entre tests: cada uno usa un email propio.
    return f"Usuario-{uuid4().hex[:8]}@Example.com"


async def test_register_creates_user_without_exposing_hash(
    client: TestClient, engine: AsyncEngine
) -> None:
    email = new_email()
    response = client.post(
        "/auth/register", json={"email": email, "password": "clave-larga-123", "name": "  Ana  "}
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "email", "name", "default_rate_type", "created_at"}
    assert body["email"] == email.lower()
    assert body["name"] == "Ana"
    assert body["default_rate_type"] == "MEP"
    async with engine.connect() as connection:
        stored = await connection.scalar(
            text("SELECT password_hash FROM users WHERE email = :email"), {"email": email.lower()}
        )
    assert str(stored).startswith("$argon2id$")


def test_register_rejects_email_already_registered_ignoring_case(client: TestClient) -> None:
    email = new_email()
    assert client.post(
        "/auth/register", json={"email": email, "password": "clave-larga-123", "name": "Ana"}
    ).is_success

    response = client.post(
        "/auth/register",
        json={"email": email.upper(), "password": "otra-clave-456", "name": "Otra"},
    )

    assert response.status_code == 409
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["detail"] == "El email ya está registrado"


def test_register_validates_password_length_without_echoing_it(client: TestClient) -> None:
    response = client.post(
        "/auth/register", json={"email": new_email(), "password": "corta123", "name": "Ana"}
    )

    assert response.status_code == 422
    assert response.json()["errors"][0]["loc"] == ["body", "password"]
    assert "corta123" not in response.text
