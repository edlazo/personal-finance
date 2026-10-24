from collections.abc import Callable, Iterator
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
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
def sign_up(client: TestClient) -> Callable[[], dict[str, str]]:
    """Registra un usuario nuevo y devuelve el header con su access token."""

    def create() -> dict[str, str]:
        email = f"cuentas-{uuid4().hex[:8]}@example.com"
        client.post("/auth/register", json={"email": email, "password": PASSWORD, "name": "Ana"})
        login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    return create


def create(client: TestClient, auth: dict[str, str], **fields: Any) -> Response:
    body = {"name": "Galicia", "type": "SAVINGS", "currency": "ARS", "initial_balance": "1500.50"}
    return client.post("/accounts", headers=auth, json=body | fields)


def test_create_account(client: TestClient, sign_up: Callable[[], dict[str, str]]) -> None:
    response = create(client, sign_up(), name="  Galicia  ")

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Galicia"
    assert body["initial_balance"] == "1500.50"
    assert body["archived_at"] is None


def test_repeated_name_is_409_but_another_user_can_use_it(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    ana, beto = sign_up(), sign_up()
    create(client, ana)

    assert create(client, ana, name="GALICIA").status_code == 409
    assert create(client, beto).status_code == 201


def test_balance_rules(client: TestClient, sign_up: Callable[[], dict[str, str]]) -> None:
    auth = sign_up()

    negative_savings = create(client, auth, initial_balance="-10.00")
    negative_broker = create(client, auth, name="IOL", type="BROKER", initial_balance="-10.00")
    three_decimals = create(client, auth, name="Efectivo", type="CASH", initial_balance="1.001")

    assert negative_savings.status_code == 422
    assert negative_savings.json()["detail"] == "Este tipo de cuenta no admite saldo negativo"
    assert negative_broker.status_code == 201
    assert three_decimals.status_code == 422


def test_creating_an_account_requires_a_token(client: TestClient) -> None:
    assert create(client, {}).status_code == 401
