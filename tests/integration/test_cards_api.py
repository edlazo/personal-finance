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


def test_purchases_in_installments_and_the_pending_ones(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    ana = sign_up()
    body = {"name": "Visa", "network": "VISA", "closing_day": 25, "due_day": 5}
    card = client.post("/credit-cards", headers=ana, json=body).json()["id"]
    url = f"/credit-cards/{card}"
    tv = {"description": "Tele", "amount": "1000", "installments": 3, "date": "2026-10-20"}

    created = client.post(f"{url}/purchases", headers=ana, json=tv)
    dollars = client.post(f"{url}/purchases", headers=ana, json=tv | {"currency": "USD"})
    pending = client.get(f"{url}/installments", headers=ana).json()

    assert created.status_code == 201
    assert [(i["number"], i["amount"]) for i in created.json()] == [
        (1, "333.34"),
        (2, "333.33"),
        (3, "333.33"),
    ]
    assert pending == created.json()
    assert dollars.status_code == 422
    assert client.get(f"{url}/installments", headers=sign_up()).status_code == 404


def test_the_statement_of_a_period(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    ana = sign_up()
    body = {"name": "Visa", "network": "VISA", "closing_day": 31, "due_day": 10}
    url = f"/credit-cards/{client.post('/credit-cards', headers=ana, json=body).json()['id']}"
    for description, day in (("Tele", "2027-01-15"), ("Libro", "2027-02-01")):
        purchase = {"description": description, "amount": "1000", "installments": 2, "date": day}
        client.post(f"{url}/purchases", headers=ana, json=purchase)

    february = client.get(f"{url}/statements/2027-02", headers=ana).json()

    # Cierre el 31: en febrero, su último día.
    assert (february["closing_date"], february["due_date"]) == ("2027-02-28", "2027-03-10")
    assert [(i["description"], i["number"]) for i in february["items"]] == [
        ("Tele", 2),
        ("Libro", 1),
    ]
    assert (february["total_ars"], february["total_usd"]) == ("1000.00", "0.00")
    assert client.get(f"{url}/statements/2027-13", headers=ana).status_code == 422
    assert client.get(f"{url}/statements/2027-02", headers=sign_up()).status_code == 404
