from collections.abc import Callable, Iterator
from decimal import Decimal
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
        email = f"patrimonio-{uuid4().hex[:8]}@example.com"
        client.post("/auth/register", json={"email": email, "password": PASSWORD, "name": "Ana"})
        login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    return create


def money(totals: dict[str, str]) -> dict[str, Decimal]:
    return {currency: Decimal(amount) for currency, amount in totals.items()}


def test_net_worth_adds_every_module_and_converts_with_my_rate(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    ana = sign_up()
    pesos = {"name": "Galicia", "type": "SAVINGS", "currency": "ARS", "initial_balance": "500000"}
    client.post("/accounts", headers=ana, json=pesos)
    dollars = {"name": "Dólares", "currency": "USD", "initial_balance": "100"}
    client.post("/accounts", headers=ana, json=pesos | dollars)
    rate = {"type": "MEP", "buy": "1000", "sell": "1000", "quoted_at": "2026-01-02T12:00:00Z"}
    client.post("/fx/rates", headers=ana, json=rate)
    visa = {"name": "Visa", "network": "VISA", "closing_day": 25, "due_day": 5}
    card = client.post("/credit-cards", headers=ana, json=visa).json()["id"]
    tv = {"description": "Tele", "amount": "30000", "installments": 3, "date": "2026-10-20"}
    client.post(f"/credit-cards/{card}/purchases", headers=ana, json=tv)
    debt = {
        "counterparty": "Banco",
        "currency": "ARS",
        "principal": "120000",
        "installments": 12,
        "start_date": "2027-01-31",
    }
    client.post("/debts", headers=ana, json=debt)
    loan = debt | {"direction": "LENT", "currency": "USD", "principal": "50", "installments": 1}
    client.post("/debts", headers=ana, json=loan)

    report = client.get("/reports/net-worth", headers=ana).json()
    in_dollars = client.get("/reports/net-worth?currency=USD", headers=ana).json()

    groups = {g["group"]: g for g in report["groups"]}
    assert report["rate_type"] == "MEP"
    assert money(groups["ACCOUNTS"]["by_currency"]) == {"ARS": 500000, "USD": 100}
    assert money(groups["ACCOUNTS"]["total"]) == {"ARS": 600000, "USD": 600}
    assert money(groups["LOANS"]["total"]) == {"ARS": 50000, "USD": 50}
    assert (groups["CARDS"]["liability"], money(groups["CARDS"]["total"])["ARS"]) == (
        True,
        Decimal("30000"),
    )
    assert money(groups["INVESTMENTS"]["total"]) == {"ARS": 0, "USD": 0}
    assert money(report["liabilities"]) == {"ARS": 150000, "USD": 150}
    assert money(report["net_worth"]) == {"ARS": 500000, "USD": 500}
    assert money(in_dollars["net_worth"]) == {"USD": 500}
    assert client.get("/reports/net-worth?currency=EUR", headers=ana).status_code == 422
    other = client.get("/reports/net-worth", headers=sign_up()).json()
    assert money(other["net_worth"]) == {"ARS": 0, "USD": 0}
