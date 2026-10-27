from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.investments.application.register_price import RegisterPrice
from app.modules.investments.domain.instrument import Instrument, InstrumentType, Market
from app.modules.investments.domain.trade import InvalidTradeError
from app.shared.domain.errors import NotFoundError
from app.shared.domain.money import Currency
from fakes.investments import FakeInvestmentsUnitOfWork

USER = uuid4()
DAY = date(2026, 10, 24)


async def test_prices_are_kept_as_history_for_own_instruments() -> None:
    uow = FakeInvestmentsUnitOfWork()
    ggal = Instrument(USER, "GGAL", "Galicia", InstrumentType.STOCK, Market.BYMA, Currency.ARS)
    uow.instruments.items.append(ggal)
    register = RegisterPrice(uow=uow)

    await register(USER, instrument_id=ggal.id, price=Decimal("6500"), on=DAY)
    await register(USER, instrument_id=ggal.id, price=Decimal("6600"), on=DAY)

    assert [p.price for p in uow.prices.items] == [Decimal("6500"), Decimal("6600")]
    assert (await uow.prices.latest_prices())[ggal.id].price == Decimal("6600")
    with pytest.raises(NotFoundError):
        await register(USER, instrument_id=uuid4(), price=Decimal("1"), on=DAY)
    with pytest.raises(InvalidTradeError):
        await register(USER, instrument_id=ggal.id, price=Decimal("0"), on=DAY)
