from datetime import date
from decimal import Decimal
from uuid import uuid4

import httpx2
import pytest

from app.modules.investments.application.sync_crypto_prices import SyncCryptoPrices
from app.modules.investments.domain.instrument import Instrument, InstrumentType, Market
from app.modules.investments.domain.price import PriceSource
from app.modules.investments.infrastructure.coingecko import CoinGeckoProvider
from app.shared.domain.money import Currency
from fakes.investments import FakePriceSyncUnitOfWork

ANA, BETO = uuid4(), uuid4()
DAY = date(2026, 10, 26)
PAYLOAD = b'{"btc": {"usd": 79697.123456789012, "ars": 121191698}, "eth": {"usd": 2313.29}}'


def coingecko(*codes: int) -> tuple[CoinGeckoProvider, list[httpx2.Request]]:
    """Responde con esos códigos en orden; el último se repite."""
    calls: list[httpx2.Request] = []

    def handle(request: httpx2.Request) -> httpx2.Response:
        calls.append(request)
        code = codes[min(len(calls), len(codes)) - 1]
        return httpx2.Response(code, content=PAYLOAD if code == 200 else b"")

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handle))
    return CoinGeckoProvider(client, "https://cg.test", api_key="demo", retry_wait=0), calls


async def test_one_call_for_every_symbol_as_decimal_per_currency() -> None:
    provider, calls = coingecko(503, 200)

    prices = await provider.prices({"BTC", "ETH"})

    assert prices == {
        "BTC": {Currency.USD: Decimal("79697.123456789012"), Currency.ARS: Decimal("121191698")},
        "ETH": {Currency.USD: Decimal("2313.29")},
    }
    assert calls[-1].url.params["symbols"] == "btc,eth"
    assert (len(calls), calls[-1].headers["x-cg-demo-api-key"]) == (2, "demo")


async def test_each_user_crypto_gets_a_price_in_its_own_currency() -> None:
    uow = FakePriceSyncUnitOfWork()
    btc_usd = Instrument(ANA, "BTC", "Bitcoin", InstrumentType.CRYPTO, Market.CRYPTO, Currency.USD)
    btc_ars = Instrument(BETO, "BTC", "Bitcoin", InstrumentType.CRYPTO, Market.CRYPTO, Currency.ARS)
    unknown = Instrument(ANA, "XYZ", "Otra", InstrumentType.CRYPTO, Market.CRYPTO, Currency.USD)
    ggal = Instrument(ANA, "GGAL", "Galicia", InstrumentType.STOCK, Market.BYMA, Currency.ARS)
    uow.store.instruments += [btc_usd, btc_ars, unknown, ggal]
    provider, calls = coingecko(200)

    saved = await SyncCryptoPrices(uow, provider)(DAY)

    by_instrument = {p.instrument_id: p for p in uow.store.prices}
    assert (saved, len(calls)) == (2, 1)
    assert by_instrument[btc_usd.id].price == Decimal("79697.1234567890")
    assert (by_instrument[btc_ars.id].price, by_instrument[btc_ars.id].user_id) == (
        Decimal("121191698"),
        BETO,
    )
    assert {p.source for p in uow.store.prices} == {PriceSource.API}
    assert await SyncCryptoPrices(FakePriceSyncUnitOfWork(), provider)(DAY) == 0


async def test_a_failing_source_raises_after_three_attempts() -> None:
    provider, calls = coingecko(429)
    with pytest.raises(httpx2.HTTPStatusError):
        await provider.prices({"BTC"})
    assert len(calls) == 3
