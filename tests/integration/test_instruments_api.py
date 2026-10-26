from collections.abc import Callable, Iterator
from decimal import Decimal
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from pydantic import PostgresDsn
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import Settings
from app.main import create_app
from app.modules.investments.infrastructure.jobs import sync_crypto_prices
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
        json={"name": "Wallet", "type": "CRYPTO_WALLET", "currency": "USD"},
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
