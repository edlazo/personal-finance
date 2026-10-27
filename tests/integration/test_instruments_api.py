from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from pydantic import PostgresDsn
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import Settings
from app.main import create_app
from app.modules.investments.application.sync_portfolio import SyncPortfolio
from app.modules.investments.domain.instrument import InstrumentType, Market
from app.modules.investments.domain.portfolio import BrokerHolding, CallBudgetExhaustedError
from app.modules.investments.infrastructure.cipher import FernetCipher
from app.modules.investments.infrastructure.credentials import (
    BrokerCredentialsModel,
    HoldingSnapshotModel,
)
from app.modules.investments.infrastructure.jobs import (
    sync_crypto_prices,
    sync_iol_portfolios,
    sync_market_prices,
)
from app.modules.investments.infrastructure.persistence import (
    InstrumentModel,
    SqlAlchemyInvestmentsUnitOfWork,
)
from app.shared.domain.money import Currency
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
        email = f"inversiones-{uuid4().hex[:8]}@example.com"
        client.post("/auth/register", json={"email": email, "password": PASSWORD, "name": "Ana"})
        login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    return create


def create(client: TestClient, auth: dict[str, str], **fields: Any) -> Response:
    body = {"ticker": "al30", "name": "Bonar 2030", "type": "BOND", "market": "BYMA"}
    return client.post("/instruments", headers=auth, json=body | {"currency": "ARS"} | fields)


def test_each_user_has_a_catalog_with_unique_tickers_per_market(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    ana, beto = sign_up(), sign_up()

    bond = create(client, ana)
    repeated = create(client, ana, ticker="AL30", type="ON")
    other_market = create(client, ana, ticker="SPY", name="S&P 500", type="ETF", market="NYSE")
    same_for_beto = create(client, beto)

    assert bond.status_code == 201
    assert (bond.json()["ticker"], bond.json()["quote_unit"]) == ("AL30", 100)
    assert repeated.status_code == 409
    assert other_market.json()["quote_unit"] == 1
    assert same_for_beto.status_code == 201
    listed = client.get("/instruments", headers=ana).json()
    assert [(i["market"], i["ticker"]) for i in listed] == [("BYMA", "AL30"), ("NYSE", "SPY")]
    assert create(client, ana, market="LSE").status_code == 422
    assert create(client, {}).status_code == 401


def test_trades_move_the_broker_account_and_respect_the_holding(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    auth = sign_up()
    broker = client.post(
        "/accounts",
        headers=auth,
        json={"name": "IOL", "type": "BROKER", "currency": "ARS", "initial_balance": "100000"},
    ).json()["id"]
    ggal = create(client, auth, ticker="GGAL", name="Galicia", type="STOCK").json()["id"]

    def trade(side: str, quantity: str, price: str, fee: str = "0") -> Response:
        body = {"account_id": broker, "instrument_id": ggal, "side": side, "quantity": quantity}
        body |= {"price": price, "fee": fee, "date": "2026-10-24"}
        return client.post("/trades", headers=auth, json=body)

    bought = trade("BUY", "10", "6500", fee="100")
    sold = trade("SELL", "4", "7000", fee="50")
    too_many = trade("SELL", "7", "7000")
    balance = client.get(f"/accounts/{broker}", headers=auth).json()["balance"]
    movements = client.get("/transactions", headers=auth).json()["items"]

    assert (bought.status_code, bought.json()["cash"]) == (201, "65100.00")
    assert sold.json()["cash"] == "27950.00"
    assert too_many.status_code == 422
    assert balance == "62850.00"
    assert {m["trade_id"] for m in movements} == {bought.json()["id"], sold.json()["id"]}
    assert trade("BUY", "1", "1", fee="0").status_code == 201
    other_user = client.post("/trades", headers=sign_up(), json={**bought.json(), "fee": "0"})
    assert other_user.status_code == 404


def test_positions_show_cost_result_and_value_in_both_currencies(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    auth = sign_up()
    broker = client.post(
        "/accounts", headers=auth, json={"name": "IOL", "type": "BROKER", "currency": "ARS"}
    ).json()["id"]
    ggal = create(client, auth, ticker="GGAL", name="Galicia", type="STOCK").json()["id"]
    rate = {"type": "MEP", "buy": "1000", "sell": "1250", "quoted_at": "2026-01-02T12:00:00Z"}
    client.post("/fx/rates", headers=auth, json=rate)
    for side, quantity, price, fee in (("BUY", "10", "100", "10"), ("SELL", "4", "150", "0")):
        body = {"account_id": broker, "instrument_id": ggal, "side": side, "date": "2026-10-24"}
        body |= {"quantity": quantity, "price": price, "fee": fee}
        client.post("/trades", headers=auth, json=body)

    body = client.get("/positions", headers=auth).json()

    [position] = body["positions"]
    assert (body["rate_type"], position["instrument"]["ticker"]) == ("MEP", "GGAL")
    assert (position["quantity"], position["average_price"]) == ("6.00000000", "101.0000000000")
    assert (position["realized_pnl"], position["valuation"]) == ("196.00", "900.00")
    assert (position["valuation_ars"], position["valuation_usd"]) == ("900.00", "0.72")
    assert position["unrealized_pnl_pct"] == "48.51"


def test_a_manual_price_values_the_position_when_it_is_the_most_recent(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    auth = sign_up()
    broker = client.post(
        "/accounts", headers=auth, json={"name": "IOL", "type": "BROKER", "currency": "ARS"}
    ).json()["id"]
    ggal = create(client, auth, ticker="GGAL", name="Galicia", type="STOCK").json()["id"]
    rate = {"type": "MEP", "buy": "1000", "sell": "1000", "quoted_at": "2026-01-02T12:00:00Z"}
    client.post("/fx/rates", headers=auth, json=rate)
    body = {"account_id": broker, "instrument_id": ggal, "side": "BUY", "quantity": "10"}
    client.post("/trades", headers=auth, json=body | {"price": "100", "date": "2026-10-20"})

    price = client.post(
        "/prices", headers=auth, json={"instrument_id": ggal, "price": "130", "date": "2026-10-24"}
    )
    other = client.post(
        "/prices",
        headers=sign_up(),
        json={"instrument_id": ggal, "price": "1", "date": "2026-10-24"},
    )
    [position] = client.get("/positions", headers=auth).json()["positions"]

    assert (price.status_code, price.json()["source"], other.status_code) == (201, "MANUAL", 404)
    assert (position["price_source"], position["price_date"]) == ("MANUAL", "2026-10-24")
    assert (position["valuation"], position["unrealized_pnl"]) == ("1300.00", "300.00")


class FixedCoinGecko:
    async def prices(self, tickers: set[str]) -> dict[str, dict[Currency, Decimal]]:
        return {"BTC": {Currency.USD: Decimal("80000.5")}}


async def test_the_hourly_job_prices_crypto_positions(
    client: TestClient, sign_up: Callable[[], dict[str, str]], engine: AsyncEngine
) -> None:
    auth = sign_up()
    wallet = client.post(
        "/accounts",
        headers=auth,
        json={
            "name": "Wallet",
            "type": "CRYPTO_WALLET",
            "currency": "USD",
            "initial_balance": "50000",
        },
    ).json()["id"]
    btc = create(
        client, auth, ticker="BTC", name="Bitcoin", type="CRYPTO", market="CRYPTO", currency="USD"
    ).json()["id"]
    rate = {"type": "MEP", "buy": "1000", "sell": "1000", "quoted_at": "2026-01-02T12:00:00Z"}
    client.post("/fx/rates", headers=auth, json=rate)
    body = {"account_id": wallet, "instrument_id": btc, "side": "BUY", "quantity": "0.5"}
    client.post("/trades", headers=auth, json=body | {"price": "70000", "date": "2026-10-20"})

    await sync_crypto_prices(create_session_factory(engine), FixedCoinGecko(), ZoneInfo("UTC"))

    [position] = client.get("/positions", headers=auth).json()["positions"]
    assert (position["price_source"], position["current_price"]) == ("API", "80000.5000000000")
    assert position["valuation"] == "40000.25"


def test_income_and_amortization_credit_the_account_and_change_the_position(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    auth = sign_up()
    broker = client.post(
        "/accounts", headers=auth, json={"name": "IOL", "type": "BROKER", "currency": "ARS"}
    ).json()["id"]
    al30 = create(client, auth).json()["id"]
    rate = {"type": "MEP", "buy": "1000", "sell": "1000", "quoted_at": "2026-01-02T12:00:00Z"}
    client.post("/fx/rates", headers=auth, json=rate)
    buy = {"account_id": broker, "instrument_id": al30, "side": "BUY", "quantity": "1000"}
    client.post("/trades", headers=auth, json=buy | {"price": "75000", "date": "2026-10-20"})

    def event(kind: str, amount: str, **extra: str) -> Response:
        body = {"account_id": broker, "instrument_id": al30, "kind": kind, "amount": amount}
        return client.post(
            "/instrument-events", headers=auth, json=body | extra | {"date": "2026-10-24"}
        )

    coupon = event("COUPON", "5000.00")
    amortization = event("AMORTIZATION", "200000.00", nominal="250")
    dividend = event("DIVIDEND", "1.00")
    balance = client.get(f"/accounts/{broker}", headers=auth).json()["balance"]
    [position] = client.get("/positions", headers=auth).json()["positions"]
    rentas = [
        m for m in client.get("/transactions", headers=auth).json()["items"] if m["category_id"]
    ]

    assert (coupon.status_code, amortization.status_code, dividend.status_code) == (201, 201, 422)
    assert balance == "-545000.00"
    assert (position["quantity"], position["realized_pnl"]) == ("750.00000000", "17500.00")
    assert [m["amount"] for m in rentas] == ["5000.00"]


def test_a_purchase_cannot_leave_a_crypto_wallet_negative(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    auth = sign_up()
    wallet = client.post(
        "/accounts",
        headers=auth,
        json={
            "name": "Wallet",
            "type": "CRYPTO_WALLET",
            "currency": "USD",
            "initial_balance": "100",
        },
    ).json()["id"]
    btc = create(
        client, auth, ticker="BTC", name="Bitcoin", type="CRYPTO", market="CRYPTO", currency="USD"
    ).json()["id"]
    body = {"account_id": wallet, "instrument_id": btc, "side": "BUY", "quantity": "0.01"}

    too_much = client.post(
        "/trades", headers=auth, json=body | {"price": "80000", "date": "2026-10-24"}
    )

    assert too_much.status_code == 422
    assert client.get(f"/accounts/{wallet}", headers=auth).json()["balance"] == "100.00"


async def test_broker_credentials_are_stored_encrypted_and_never_returned(
    client: TestClient, sign_up: Callable[[], dict[str, str]], engine: AsyncEngine
) -> None:
    ana, beto = sign_up(), sign_up()
    secret_password = f"clave-iol-{uuid4().hex}"
    url = "/brokers/IOL/credentials"

    saved = client.put(url, headers=ana, json={"username": "elias", "password": secret_password})
    status = client.get(url, headers=ana)
    others = client.get(url, headers=beto).json()
    async with engine.connect() as connection:
        rows = (await connection.execute(select(BrokerCredentialsModel.secret))).scalars().all()

    assert (saved.status_code, saved.content) == (204, b"")
    assert (status.json()["configured"], status.json()["username_hint"]) == (True, "el***")
    assert secret_password not in status.text
    assert others["configured"] is False
    assert (others["username_hint"], others["updated_at"]) == (None, None)
    assert all(secret_password.encode() not in row for row in rows)
    assert (
        client.delete(url, headers=ana).status_code
        == client.delete(url, headers=ana).status_code
        == 204
    )
    assert client.get(url, headers=ana).json()["configured"] is False
    assert client.put(url, json={"username": "x", "password": "y"}).status_code == 401
    assert client.get("/brokers/BALANZ/credentials", headers=ana).status_code == 422


def test_linking_a_broker_account_blocks_manual_trades(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    auth = sign_up()

    def new_account(name: str, kind: str) -> str:
        body = {"name": name, "type": kind, "currency": "ARS", "initial_balance": "1000"}
        account_id: str = client.post("/accounts", headers=auth, json=body).json()["id"]
        return account_id

    iol, caja = new_account("IOL", "BROKER"), new_account("Caja", "CASH")
    ggal = create(client, auth, ticker="GGAL", name="Galicia", type="STOCK").json()["id"]
    url = "/brokers/IOL/account"

    wrong = client.put(url, headers=auth, json={"account_id": caja})
    linked = client.put(url, headers=auth, json={"account_id": iol})
    status = client.get("/brokers/IOL/credentials", headers=auth).json()
    body = {"account_id": iol, "instrument_id": ggal, "side": "BUY", "quantity": "1"}
    trade = client.post("/trades", headers=auth, json=body | {"price": "1", "date": "2026-10-26"})

    assert (wrong.status_code, linked.status_code) == (422, 204)
    assert (status["linked_account_id"], status["configured"]) == (iol, False)
    assert trade.status_code == 422
    assert "vinculada a IOL" in trade.json()["detail"]


async def test_the_linked_account_shows_the_saved_portfolio_snapshot(
    client: TestClient, sign_up: Callable[[], dict[str, str]], engine: AsyncEngine
) -> None:
    auth = sign_up()
    body = {"name": "IOL", "type": "BROKER", "currency": "ARS", "initial_balance": "0"}
    iol = client.post("/accounts", headers=auth, json=body).json()["id"]
    ggal = create(client, auth, ticker="GGAL", name="Galicia", type="STOCK").json()["id"]
    rate = {"type": "MEP", "buy": "1000", "sell": "1000", "quoted_at": "2026-01-02T12:00:00Z"}
    client.post("/fx/rates", headers=auth, json=rate)
    client.put("/brokers/IOL/account", headers=auth, json={"account_id": iol})
    snapshot = {
        "account_id": iol,
        "instrument_id": ggal,
        "quantity": Decimal("10"),
        "average_price": Decimal("6000"),
        "last_price": Decimal("6500"),
        "taken_at": datetime(2026, 10, 26, 15, tzinfo=UTC),
    }
    async with engine.begin() as connection:
        owner = select(InstrumentModel.user_id).where(InstrumentModel.id == ggal)
        user_id = (await connection.execute(owner)).scalar_one()
        await connection.execute(
            insert(HoldingSnapshotModel).values(snapshot | {"id": uuid4(), "user_id": user_id})
        )

    [position] = client.get("/positions", headers=auth).json()["positions"]
    others = client.get("/positions", headers=sign_up()).json()["positions"]

    assert (position["price_source"], position["price_date"]) == ("IOL", "2026-10-26")
    assert (position["cost"], position["valuation"]) == ("60000.00", "65000.00")
    assert others == []


async def test_the_iol_sync_saves_the_snapshot_within_the_monthly_limit(
    client: TestClient, sign_up: Callable[[], dict[str, str]], engine: AsyncEngine
) -> None:
    auth = sign_up()
    body = {"name": "IOL", "type": "BROKER", "currency": "ARS", "initial_balance": "0"}
    iol = client.post("/accounts", headers=auth, json=body).json()["id"]
    client.put("/brokers/IOL/account", headers=auth, json={"account_id": iol})
    login = {"username": "elias", "password": "clave"}
    client.put("/brokers/IOL/credentials", headers=auth, json=login)
    user_id = UUID(client.get("/me", headers=auth).json()["id"])
    state = client.app.state  # type: ignore[attr-defined]
    cipher = FernetCipher(state.settings.credentials_key.get_secret_value())
    uow = SqlAlchemyInvestmentsUnitOfWork(
        create_session_factory(engine), user_id, state.cash_movements
    )
    sync = SyncPortfolio(uow, FixedIol(), cipher, monthly_limit=3)

    saved = await sync(user_id, datetime(2026, 10, 26, 15, tzinfo=UTC))
    with pytest.raises(CallBudgetExhaustedError):
        await sync(user_id, datetime(2026, 10, 26, 16, tzinfo=UTC))

    rate = {"type": "MEP", "buy": "1000", "sell": "1000", "quoted_at": "2026-01-02T12:00:00Z"}
    client.post("/fx/rates", headers=auth, json=rate)
    [position] = client.get("/positions", headers=auth).json()["positions"]
    assert saved == 1
    assert (position["instrument"]["ticker"], position["price_source"]) == ("GGAL", "IOL")
    assert position["valuation"] == "65000.00"


class FixedIol:
    async def portfolio(self, username: str, password: str) -> list[BrokerHolding]:
        assert (username, password) == ("elias", "clave")
        amounts = (Decimal("10"), Decimal("6000"), Decimal("6500"))
        stock, ars = InstrumentType.STOCK, Currency.ARS
        return [BrokerHolding("GGAL", "Galicia", stock, Market.BYMA, ars, *amounts)]


async def test_the_iol_job_syncs_each_linked_user_even_if_another_fails(
    client: TestClient, sign_up: Callable[[], dict[str, str]], engine: AsyncEngine
) -> None:
    def linked_user(username: str) -> dict[str, str]:
        auth = sign_up()
        body = {"name": "IOL", "type": "BROKER", "currency": "ARS", "initial_balance": "0"}
        iol = client.post("/accounts", headers=auth, json=body).json()["id"]
        client.put("/brokers/IOL/account", headers=auth, json={"account_id": iol})
        login = {"username": username, "password": "clave"}
        client.put("/brokers/IOL/credentials", headers=auth, json=login)
        rate = {"type": "MEP", "buy": "1000", "sell": "1000", "quoted_at": "2026-01-02T12:00:00Z"}
        client.post("/fx/rates", headers=auth, json=rate)
        return auth

    broken, ok = linked_user("otro"), linked_user("elias")
    state = client.app.state  # type: ignore[attr-defined]
    cipher = FernetCipher(state.settings.credentials_key.get_secret_value())
    factory = create_session_factory(engine)

    await sync_iol_portfolios(
        factory, OnlyElias(), cipher, state.cash_movements, 100, ZoneInfo("UTC")
    )

    assert client.get("/positions", headers=broken).json()["positions"] == []
    [position] = client.get("/positions", headers=ok).json()["positions"]
    assert position["price_source"] == "IOL"


class OnlyElias(FixedIol):
    async def portfolio(self, username: str, password: str) -> list[BrokerHolding]:
        if username != "elias":
            raise RuntimeError("IOL rechazó las credenciales")
        return await super().portfolio(username, password)


async def test_the_market_job_price_beats_a_newer_manual_one(
    client: TestClient, sign_up: Callable[[], dict[str, str]], engine: AsyncEngine
) -> None:
    auth = sign_up()
    body = {"name": "Broker", "type": "BROKER", "currency": "ARS", "initial_balance": "100000"}
    broker = client.post("/accounts", headers=auth, json=body).json()["id"]
    ggal = create(client, auth, ticker="GGAL", name="Galicia", type="STOCK").json()["id"]
    trade = {"account_id": broker, "instrument_id": ggal, "side": "BUY", "quantity": "1"}
    client.post("/trades", headers=auth, json=trade | {"price": "6000", "date": "2026-10-01"})
    rate = {"type": "MEP", "buy": "1000", "sell": "1000", "quoted_at": "2026-01-02T12:00:00Z"}
    client.post("/fx/rates", headers=auth, json=rate)
    future = {"instrument_id": ggal, "price": "1", "date": "2099-01-01"}
    client.post("/prices", headers=auth, json=future)

    await sync_market_prices(create_session_factory(engine), FixedData912(), ZoneInfo("UTC"))

    [position] = client.get("/positions", headers=auth).json()["positions"]
    assert (position["price_source"], position["current_price"]) == ("API", "6500.0000000000")


class FixedData912:
    async def market_prices(self) -> dict[tuple[Market, str], dict[Currency, Decimal]]:
        return {(Market.BYMA, "GGAL"): {Currency.ARS: Decimal("6500")}}
