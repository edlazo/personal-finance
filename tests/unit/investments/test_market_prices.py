import json
from datetime import date
from decimal import Decimal
from uuid import uuid4

import httpx2

from app.modules.investments.application.sync_market_prices import SyncMarketPrices
from app.modules.investments.domain.instrument import Instrument, InstrumentType, Market
from app.modules.investments.domain.position import build_positions
from app.modules.investments.domain.price import InstrumentPrice, PriceSource
from app.modules.investments.domain.trade import Trade, TradeSide
from app.modules.investments.infrastructure.data912 import Data912Provider
from app.shared.domain.money import Currency
from fakes.investments import FakePriceSyncUnitOfWork, InMemoryPrices

ANA = uuid4()
PANELS = {
    "arg_stocks": [{"symbol": "GGAL", "c": 6500.5}, {"symbol": "SIN", "c": 0}],
    "arg_cedears": [{"symbol": "AMD", "c": 21000}, {"symbol": "SPY", "c": 50000}],
    "arg_bonds": [{"symbol": "GD30", "c": 88320}, {"symbol": "GD30D", "c": 56.47}],
    "usa_adrs": [{"symbol": "GGAL", "c": 45.1}],
}


def data912() -> tuple[Data912Provider, list[str]]:
    paths: list[str] = []

    def handle(request: httpx2.Request) -> httpx2.Response:
        paths.append(request.url.path)
        panel = PANELS.get(request.url.path.removeprefix("/live/"), [])
        return httpx2.Response(200, content=json.dumps(panel).encode())

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handle))
    return Data912Provider(client, "https://data912.test"), paths


async def test_each_panel_is_read_once_and_keyed_by_market_and_currency() -> None:
    provider, paths = data912()

    quotes = await provider.market_prices()

    assert len(paths) == 7
    assert quotes[(Market.BYMA, "GGAL")] == {Currency.ARS: Decimal("6500.5")}
    assert quotes[(Market.BYMA, "GD30")] == {Currency.ARS: Decimal("88320")}
    assert quotes[(Market.BYMA, "GD30D")] == {Currency.USD: Decimal("56.47")}
    # AMD es un CEDEAR en pesos: termina en D pero no hay un "AM".
    assert quotes[(Market.BYMA, "AMD")] == {Currency.ARS: Decimal("21000")}
    assert quotes[(Market.NASDAQ, "GGAL")] == quotes[(Market.NYSE, "GGAL")]
    assert (Market.BYMA, "SIN") not in quotes


async def test_only_instruments_quoted_in_their_currency_get_a_price() -> None:
    uow = FakePriceSyncUnitOfWork()

    def instrument(ticker: str, market: Market, currency: Currency) -> Instrument:
        return Instrument(ANA, ticker, ticker, InstrumentType.BOND, market, currency)

    gd30d, wrong, adr = (
        instrument("GD30D", Market.BYMA, Currency.USD),
        instrument("GD30", Market.BYMA, Currency.USD),
        instrument("GGAL", Market.NASDAQ, Currency.USD),
    )
    uow.store.instruments += [gd30d, wrong, adr]

    saved = await SyncMarketPrices(uow, data912()[0])(date(2026, 10, 26))

    assert saved == 2
    assert {(p.instrument_id, p.price, p.source) for p in uow.store.prices} == {
        (gd30d.id, Decimal("56.4700000000"), PriceSource.API),
        (adr.id, Decimal("45.1000000000"), PriceSource.API),
    }


async def test_an_automatic_price_beats_a_newer_manual_one() -> None:
    ggal = Instrument(ANA, "GGAL", "Galicia", InstrumentType.STOCK, Market.BYMA, Currency.ARS)
    prices = InMemoryPrices()
    await prices.add(InstrumentPrice(ANA, ggal.id, Decimal("100"), date(2026, 10, 26)))
    api = InstrumentPrice(ANA, ggal.id, Decimal("90"), date(2026, 10, 25), PriceSource.API)
    await prices.add(api)
    buy = Trade(
        ANA,
        uuid4(),
        ggal.id,
        TradeSide.BUY,
        Decimal("1"),
        Decimal("80"),
        Decimal("0"),
        date(2026, 10, 1),
    )

    [position] = build_positions([buy], {ggal.id: ggal}, await prices.latest_prices())

    assert (position.current_price, position.price_source) == (Decimal("90"), "API")
