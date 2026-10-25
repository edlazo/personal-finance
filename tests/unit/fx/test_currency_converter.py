from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.modules.fx.application.currency_converter import CurrencyConverter
from app.modules.fx.domain.rate import ExchangeRate, RateSource
from app.shared.domain.money import Currency
from app.shared.domain.rates import MoneyConverter, RateNotAvailableError, RateType
from fakes.fx import FakeFxUnitOfWork

ARS, USD = Currency.ARS, Currency.USD
MONDAY = datetime(2026, 10, 19, 15, 0, tzinfo=UTC)


def converter(*rates: tuple[datetime, str, str]) -> MoneyConverter:
    uow = FakeFxUnitOfWork()
    uow.rates.items = [
        ExchangeRate(RateType.MEP, Decimal(buy), Decimal(sell), at, RateSource.API)
        for at, buy, sell in rates
    ]
    return CurrencyConverter(uow=uow)


async def test_buys_dollars_at_the_sell_price_and_sells_them_at_the_buy_price() -> None:
    mep = converter((MONDAY, "1200", "1250"))

    async def convert(amount: str, source: Currency, target: Currency) -> Decimal:
        return await mep.convert(Decimal(amount), source, target, rate_type=RateType.MEP, at=MONDAY)

    assert await convert("100000", ARS, USD) == Decimal("80.00")
    assert await convert("100", USD, ARS) == Decimal("120000.00")
    assert await convert("1000", ARS, USD) == Decimal("0.80")
    assert await convert("1500.50", ARS, ARS) == Decimal("1500.50")
    rate = ExchangeRate(RateType.MEP, Decimal("1"), Decimal("2"), MONDAY, RateSource.API)
    assert rate.convert(Decimal("3.333"), USD, USD) == Decimal("3.333")


async def test_uses_the_latest_rate_not_after_the_date() -> None:
    mep = converter((MONDAY, "1000", "1000"), (MONDAY + timedelta(days=2), "2000", "2000"))

    tuesday = await mep.convert(
        Decimal("10"), USD, ARS, rate_type=RateType.MEP, at=MONDAY + timedelta(days=1)
    )

    assert tuesday == Decimal("10000.00")
    with pytest.raises(RateNotAvailableError, match="No hay cotización MEP"):
        await mep.convert(Decimal("10"), USD, ARS, rate_type=RateType.MEP, at=MONDAY - timedelta(1))
    with pytest.raises(RateNotAvailableError, match="BLUE"):
        await mep.convert(Decimal("10"), USD, ARS, rate_type=RateType.BLUE, at=MONDAY)
