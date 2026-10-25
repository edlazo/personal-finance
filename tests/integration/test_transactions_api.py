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
    def create() -> dict[str, str]:
        email = f"movimientos-{uuid4().hex[:8]}@example.com"
        client.post("/auth/register", json={"email": email, "password": PASSWORD, "name": "Ana"})
        login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    return create


def setup(client: TestClient, auth: dict[str, str]) -> tuple[str, dict[str, str]]:
    """Crea una cuenta y devuelve su id y las categorías por nombre y tipo."""
    account = client.post(
        "/accounts", headers=auth, json={"name": "Galicia", "type": "SAVINGS", "currency": "ARS"}
    )
    categories = {
        f"{c['kind']}:{c['name']}": c["id"] for c in client.get("/categories", headers=auth).json()
    }
    return account.json()["id"], categories


def expense(
    client: TestClient, auth: dict[str, str], account_id: str, category_id: str, **fields: Any
) -> Response:
    body = {
        "account_id": account_id,
        "kind": "EXPENSE",
        "amount": "1500.50",
        "date": "2026-10-24",
        "category_id": category_id,
        "description": "Compra del mes",
    }
    return client.post("/transactions", headers=auth, json=body | fields)


def test_register_an_expense_and_its_rules(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    auth = sign_up()
    account_id, categories = setup(client, auth)
    supermercado = categories["EXPENSE:Supermercado"]

    created = expense(client, auth, account_id, supermercado)
    wrong_kind = expense(client, auth, account_id, categories["INCOME:Sueldo"])
    zero = expense(client, auth, account_id, supermercado, amount="0")
    currency = client.patch(f"/accounts/{account_id}", headers=auth, json={"currency": "USD"})
    client.delete(f"/accounts/{account_id}", headers=auth)
    archived = expense(client, auth, account_id, supermercado)

    assert created.status_code == 201
    assert created.json()["amount"] == "1500.50"
    assert wrong_kind.status_code == 422
    assert wrong_kind.json()["detail"] == "La categoría no coincide con el tipo del movimiento"
    assert zero.status_code == 422
    assert currency.status_code == 409
    assert archived.status_code == 422


def test_another_users_account_is_404_and_a_token_is_required(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    ana, beto = sign_up(), sign_up()
    account_id, _ = setup(client, ana)
    _, beto_categories = setup(client, beto)

    response = expense(client, beto, account_id, beto_categories["EXPENSE:Supermercado"])

    assert response.status_code == 404
    assert expense(client, {}, account_id, str(uuid4())).status_code == 401


def test_balance_is_derived_from_movements_and_supports_as_of(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    auth = sign_up()
    account = client.post(
        "/accounts",
        headers=auth,
        json={"name": "Caja", "type": "CASH", "currency": "ARS", "initial_balance": "1000.00"},
    ).json()
    categories = {
        f"{c['kind']}:{c['name']}": c["id"] for c in client.get("/categories", headers=auth).json()
    }
    sueldo = {"kind": "INCOME", "amount": "500.00", "date": "2026-10-01"}
    expense(client, auth, account["id"], categories["INCOME:Sueldo"], **sueldo)
    expense(client, auth, account["id"], categories["EXPENSE:Ocio"], amount="200.50")

    today = client.get(f"/accounts/{account['id']}", headers=auth).json()
    before = client.get("/accounts", headers=auth, params={"as_of": "2026-10-10"}).json()

    assert today["balance"] == "1299.50"
    assert [a["balance"] for a in before if a["id"] == account["id"]] == ["1500.00"]


def test_list_filters_paginates_and_sorts_newest_first(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    auth = sign_up()
    account_id, categories = setup(client, auth)
    sueldo, super_ = categories["INCOME:Sueldo"], categories["EXPENSE:Supermercado"]
    old = expense(client, auth, account_id, super_, date="2026-09-30", amount="100.00").json()
    pay = expense(client, auth, account_id, sueldo, kind="INCOME", description="Sueldo 100%")
    new = expense(client, auth, account_id, super_, date="2026-10-24", amount="2000.00").json()

    def ids(**params: Any) -> list[str]:
        body = client.get("/transactions", headers=auth, params=params).json()
        return [t["id"] for t in body["items"]]

    page = client.get("/transactions", headers=auth, params={"limit": 2}).json()
    assert (page["total"], len(page["items"]), page["items"][-1]["date"]) == (3, 2, "2026-10-24")
    assert ids(offset=2) == ids(date_to="2026-09-30") == [old["id"]]
    assert ids(date_from="2026-10-01", kind="EXPENSE") == [new["id"]]
    assert ids(category_id=super_, amount_min="100.00", amount_max="1999.99") == [old["id"]]
    assert ids(q="100%", account_id=account_id) == [pay.json()["id"]]
    assert ids(q="_") == []
    assert client.get("/transactions", headers=sign_up()).json()["total"] == 0


def test_transfer_moves_money_between_own_accounts(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    auth = sign_up()
    galicia, _ = setup(client, auth)
    caja = client.post(
        "/accounts", headers=auth, json={"name": "Caja", "type": "CASH", "currency": "ARS"}
    ).json()["id"]
    usd = client.post(
        "/accounts", headers=auth, json={"name": "Dólares", "type": "CASH", "currency": "USD"}
    ).json()["id"]

    def send(source: str, target: str, headers: dict[str, str] = auth) -> Response:
        body = {"from_account_id": source, "to_account_id": target, "amount": "300.00"}
        return client.post("/transfers", headers=headers, json=body | {"date": "2026-10-24"})

    created = send(galicia, caja)
    balances = {a["name"]: a["balance"] for a in client.get("/accounts", headers=auth).json()}
    listed = client.get("/transactions", headers=auth).json()["items"]

    assert created.status_code == 201
    group = created.json()["transfer_group_id"]
    assert balances == {"Galicia": "-300.00", "Caja": "300.00", "Dólares": "0.00"}
    assert [(t["category_id"], t["transfer_group_id"]) for t in listed] == [(None, group)] * 2
    assert send(galicia, galicia).status_code == 422
    assert send(galicia, usd).status_code == 422
    assert send(galicia, caja, headers=sign_up()).status_code == 404
