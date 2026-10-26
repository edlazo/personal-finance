from collections.abc import Callable, Iterator
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
def sign_up(client: TestClient) -> Callable[[], dict[str, str]]:
    def create() -> dict[str, str]:
        email = f"tarjetas-{uuid4().hex[:8]}@example.com"
        client.post("/auth/register", json={"email": email, "password": PASSWORD, "name": "Ana"})
        login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    return create


def test_each_user_registers_and_sees_only_their_cards(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    ana, beto = sign_up(), sign_up()
    body = {"name": "Visa Galicia", "network": "VISA", "closing_day": 25, "due_day": 5}

    created = client.post(
        "/credit-cards", headers=ana, json=body | {"dual_currency": True, "limit": "800000.50"}
    )
    card = created.json()
    invalid = client.post("/credit-cards", headers=ana, json=body | {"closing_day": 32})

    assert created.status_code == 201
    assert (card["currencies"], card["limit"]) == (["ARS", "USD"], "800000.50")
    assert client.get(f"/credit-cards/{card['id']}", headers=ana).json() == card
    assert client.get("/credit-cards", headers=ana).json() == [card]
    assert client.get("/credit-cards", headers=beto).json() == []
    assert client.get(f"/credit-cards/{card['id']}", headers=beto).status_code == 404
    assert invalid.status_code == 422
    assert client.get("/credit-cards").status_code == 401
