from collections.abc import Callable, Iterator
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from pydantic import PostgresDsn
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import Settings
from app.main import create_app
from app.modules.ledger.infrastructure.cash_movements import LedgerCashMovements
from app.shared.domain.errors import NotFoundError
from app.shared.infrastructure.database import create_session_factory

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
        "/accounts",
        headers=auth,
        # Con saldo: un gasto no puede dejar la cuenta en negativo (US-062).
        json={
            "name": "Galicia",
            "type": "SAVINGS",
            "currency": "ARS",
            "initial_balance": "1000000",
        },
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
    assert balances == {"Galicia": "999700.00", "Caja": "300.00", "Dólares": "0.00"}
    assert [(t["category_id"], t["transfer_group_id"]) for t in listed] == [(None, group)] * 2
    assert send(galicia, galicia).status_code == 422
    assert send(galicia, usd).status_code == 422
    assert send(galicia, caja, headers=sign_up()).status_code == 404


def test_edit_and_delete_movements_and_transfers(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    auth = sign_up()
    galicia, categories = setup(client, auth)
    movement = expense(client, auth, galicia, categories["EXPENSE:Ocio"]).json()["id"]
    caja = client.post(
        "/accounts", headers=auth, json={"name": "Caja", "type": "CASH", "currency": "ARS"}
    ).json()["id"]
    body = {"from_account_id": galicia, "to_account_id": caja, "amount": "300.00"}
    legs = client.post("/transfers", headers=auth, json=body | {"date": "2026-10-24"}).json()

    edited = client.patch(
        f"/transactions/{movement}",
        headers=auth,
        json={"amount": "99.90", "category_id": categories["EXPENSE:Supermercado"]},
    )
    moved = client.patch(
        f"/transactions/{legs['incoming']['id']}", headers=auth, json={"amount": "250.00"}
    )
    balances = {a["name"]: a["balance"] for a in client.get("/accounts", headers=auth).json()}

    assert (edited.status_code, edited.json()["amount"]) == (200, "99.90")
    assert moved.json()["amount"] == "250.00"
    assert balances == {"Galicia": "999650.10", "Caja": "250.00"}
    other = sign_up()
    assert client.delete(f"/transactions/{movement}", headers=other).status_code == 404
    assert client.delete(f"/transactions/{legs['outgoing']['id']}", headers=auth).status_code == 204
    assert client.delete(f"/transactions/{movement}", headers=auth).status_code == 204
    assert client.get("/transactions", headers=auth).json()["total"] == 0


def test_buying_dollars_with_a_fee(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    auth = sign_up()
    galicia, _ = setup(client, auth)
    dolares = client.post(
        "/accounts", headers=auth, json={"name": "Dólares", "type": "SAVINGS", "currency": "USD"}
    ).json()["id"]
    body = {"from_account_id": galicia, "to_account_id": dolares, "date": "2026-10-24"}

    bought = client.post(
        "/transfers",
        headers=auth,
        json=body | {"amount": "125000.00", "to_amount": "100.00", "fee": "500.00"},
    )
    missing = client.post("/transfers", headers=auth, json=body | {"amount": "10.00"})
    edited = client.patch(
        f"/transactions/{bought.json()['incoming']['id']}", headers=auth, json={"amount": "99.50"}
    )
    balances = {a["name"]: a["balance"] for a in client.get("/accounts", headers=auth).json()}
    fee_category = client.get("/categories", headers=auth).json()

    assert bought.status_code == 201
    assert (bought.json()["exchange_rate"], bought.json()["fee"]["amount"]) == (
        "1250.0000",
        "500.00",
    )
    names = {c["id"]: c["name"] for c in fee_category}
    assert names[bought.json()["fee"]["category_id"]] == "Comisiones"
    assert missing.status_code == 422
    assert edited.json()["amount"] == "99.50"
    assert balances == {"Galicia": "874500.00", "Dólares": "99.50"}


async def test_other_modules_move_cash_through_ledger(
    client: TestClient, sign_up: Callable[[], dict[str, str]], engine: AsyncEngine
) -> None:
    auth = sign_up()
    user_id = UUID(client.get("/me", headers=auth).json()["id"])
    broker = client.post(
        "/accounts", headers=auth, json={"name": "IOL", "type": "BROKER", "currency": "ARS"}
    ).json()["id"]
    trade_id = uuid4()

    async with create_session_factory(engine)() as session:
        cash = LedgerCashMovements(session, user_id)
        account = await cash.account(UUID(broker))
        await cash.record_trade(
            account.id,
            Decimal("1500.00"),
            incoming=False,
            on=date(2026, 10, 24),
            trade_id=trade_id,
            description="Compra 10 GGAL",
        )
        await session.commit()
        with pytest.raises(NotFoundError):
            await LedgerCashMovements(session, uuid4()).account(UUID(broker))

    [movement] = client.get("/transactions", headers=auth).json()["items"]
    balance = client.get(f"/accounts/{broker}", headers=auth).json()["balance"]
    assert (account.holds_investments, account.archived) == (True, False)
    assert (movement["trade_id"], movement["category_id"], balance) == (
        str(trade_id),
        None,
        "-1500.00",
    )
    patch = client.patch(f"/transactions/{movement['id']}", headers=auth, json={"amount": "1.00"})
    assert (
        patch.status_code,
        client.delete(f"/transactions/{movement['id']}", headers=auth).status_code,
    ) == (422, 422)


async def test_income_from_investments_lands_in_rentas_and_is_read_only(
    client: TestClient, sign_up: Callable[[], dict[str, str]], engine: AsyncEngine
) -> None:
    auth = sign_up()
    user_id = UUID(client.get("/me", headers=auth).json()["id"])
    broker = client.post(
        "/accounts", headers=auth, json={"name": "IOL", "type": "BROKER", "currency": "ARS"}
    ).json()["id"]

    async with create_session_factory(engine)() as session:
        # Usuario nuevo: todavía no tiene categorías, se crean las por defecto en el primer uso.
        await LedgerCashMovements(session, user_id).record_income(
            UUID(broker),
            Decimal("250.00"),
            on=date(2026, 10, 24),
            trade_id=uuid4(),
            description="Dividendo GGAL",
        )
        await session.commit()

    [movement] = client.get("/transactions", headers=auth).json()["items"]
    categories = {c["id"]: c for c in client.get("/categories", headers=auth).json()}
    rentas = categories[movement["category_id"]]
    assert (rentas["name"], rentas["kind"], movement["kind"]) == ("Rentas", "INCOME", "INCOME")
    assert (len(categories), movement["trade_id"] is not None) == (14, True)
    assert client.delete(f"/transactions/{movement['id']}", headers=auth).status_code == 422
    client.delete(f"/categories/{rentas['id']}", headers=auth)
    async with create_session_factory(engine)() as session:
        await LedgerCashMovements(session, user_id).record_income(
            UUID(broker),
            Decimal("10.00"),
            on=date(2026, 10, 25),
            trade_id=uuid4(),
            description="Cupón AL30",
        )
        await session.commit()
    newest = client.get("/transactions", headers=auth).json()["items"][0]
    assert newest["category_id"] != rentas["id"]


def test_an_expense_beyond_the_balance_is_rejected_except_in_a_broker(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    auth = sign_up()
    _, categories = setup(client, auth)
    caja, iol = (
        client.post(
            "/accounts",
            headers=auth,
            json={"name": name, "type": kind, "currency": "ARS", "initial_balance": "100.00"},
        ).json()["id"]
        for name, kind in (("Caja", "CASH"), ("IOL", "BROKER"))
    )

    rejected = expense(client, auth, caja, categories["EXPENSE:Ocio"], amount="100.01")
    allowed = expense(client, auth, iol, categories["EXPENSE:Ocio"], amount="500.00")

    assert rejected.status_code == 422
    assert "Caja quedaría con saldo negativo el 24/10/2026" in rejected.json()["detail"]
    assert allowed.status_code == 201
