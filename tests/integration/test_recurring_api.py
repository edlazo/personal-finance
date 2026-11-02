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
        email = f"recurrentes-{uuid4().hex[:8]}@example.com"
        client.post("/auth/register", json={"email": email, "password": PASSWORD, "name": "Ana"})
        login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    return create


def test_recurring_rules_crud_and_pause(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    ana = sign_up()
    pesos = {"name": "Galicia", "type": "SAVINGS", "currency": "ARS", "initial_balance": "0"}
    account = client.post("/accounts", headers=ana, json=pesos).json()["id"]
    garage = {"name": "Cochera", "kind": "EXPENSE"}
    category = client.post("/categories", headers=ana, json=garage).json()["id"]
    body = {
        "account_id": account,
        "kind": "EXPENSE",
        "amount": "500000",
        "category_id": category,
        "frequency": "MONTHLY",
        "start_date": "2026-11-10",
        "end_date": "2027-10-10",
        "description": "Cochera del depto",
    }

    created = client.post("/recurring", headers=ana, json=body)
    url = f"/recurring/{created.json()['id']}"
    edited = client.patch(url, headers=ana, json={"paused": True, "end_date": None}).json()

    assert created.status_code == 201
    assert (edited["paused"], edited["end_date"], edited["amount"]) == (True, None, "500000.00")
    assert client.get("/recurring", headers=ana).json() == [edited]
    for wrong in ({"kind": "INCOME"}, {"frequency": "DAILY"}):
        assert client.post("/recurring", headers=ana, json=body | wrong).status_code == 422
    assert client.patch(url, headers=ana, json={"amount": "0"}).status_code == 422
    assert client.get(url, headers=sign_up()).status_code == 404
    assert client.delete(url, headers=ana).status_code == 204
    assert client.get(url, headers=ana).status_code == 404
