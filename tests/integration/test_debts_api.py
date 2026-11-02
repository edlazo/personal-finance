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
        email = f"deudas-{uuid4().hex[:8]}@example.com"
        client.post("/auth/register", json={"email": email, "password": PASSWORD, "name": "Ana"})
        login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    return create


def test_debts_and_loans_with_their_schedule(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    ana, beto = sign_up(), sign_up()
    loan = {
        "counterparty": "Banco Galicia",
        "currency": "ARS",
        "principal": "120000",
        "installments": 12,
        "start_date": "2027-01-31",
        "annual_rate": "60",
    }

    created = client.post("/debts", headers=ana, json=loan)
    lent = client.post(
        "/debts",
        headers=ana,
        json=loan | {"counterparty": "Juan", "direction": "LENT", "annual_rate": None},
    )
    both = client.post("/debts", headers=ana, json=loan | {"fixed_installment": "11000"})
    debt = created.json()

    assert created.status_code == 201
    assert [(i["number"], i["due_date"], i["amount"]) for i in debt["schedule"][:2]] == [
        (1, "2027-02-28", "13539.05"),
        (2, "2027-03-31", "13539.05"),
    ]
    assert lent.json()["schedule"][0]["interest"] == "0.00"
    assert both.status_code == 422
    assert client.get(f"/debts/{debt['id']}", headers=ana).json() == debt
    assert [d["direction"] for d in client.get("/debts", headers=ana).json()] == ["OWED", "LENT"]
    assert client.get("/debts", headers=beto).json() == []
    assert client.get(f"/debts/{debt['id']}", headers=beto).status_code == 404


def test_paying_a_debt_shows_the_pending_balance_and_the_next_installment(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    ana = sign_up()
    pesos = {"name": "Galicia", "type": "SAVINGS", "currency": "ARS", "initial_balance": "2000"}
    account = client.post("/accounts", headers=ana, json=pesos).json()["id"]
    body = {
        "counterparty": "Juan",
        "currency": "ARS",
        "principal": "3000",
        "installments": 3,
        "start_date": "2027-01-10",
    }
    url = f"/debts/{client.post('/debts', headers=ana, json=body).json()['id']}"
    payment = {"account_id": account, "amount": "1500", "date": "2027-02-10"}

    paid = client.post(f"{url}/payments", headers=ana, json=payment)
    too_much = client.post(f"{url}/payments", headers=ana, json=payment | {"amount": "1600"})
    other = client.post(f"{url}/payments", headers=sign_up(), json=payment)
    # Quedan 500 en la cuenta, que no puede quedar en negativo.
    broke = client.post(f"{url}/payments", headers=ana, json=payment | {"amount": "600"})
    [debt] = client.get("/debts", headers=ana).json()

    assert [r.status_code for r in (paid, too_much, other, broke)] == [201, 422, 404, 422]
    assert "1500.00" in too_much.json()["detail"]
    assert (debt["paid"], debt["pending"]) == ("1500.00", "1500.00")
    assert (debt["next_installment"]["number"], debt["next_installment"]["due_date"]) == (
        2,
        "2027-03-10",
    )
    schedule = client.get(url, headers=ana).json()["schedule"]
    assert [i["paid"] for i in schedule] == [True, False, False]
    assert client.get(f"/accounts/{account}", headers=ana).json()["balance"] == "500.00"
