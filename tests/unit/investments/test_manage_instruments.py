from uuid import uuid4

import pytest

from app.modules.investments.application.manage_instruments import (
    CreateInstrument,
    ListInstruments,
)
from app.modules.investments.domain.instrument import (
    Instrument,
    InstrumentTickerTakenError,
    InstrumentType,
    InvalidInstrumentError,
    Market,
)
from app.shared.domain.money import Currency
from fakes.investments import FakeInvestmentsUnitOfWork

USER = uuid4()


async def test_ticker_is_upper_case_and_unique_per_market() -> None:
    uow = FakeInvestmentsUnitOfWork()
    create = CreateInstrument(uow=uow)

    ggal = await create(
        USER,
        ticker=" ggal ",
        name="Galicia",
        instrument_type=InstrumentType.STOCK,
        market=Market.BYMA,
        currency=Currency.ARS,
    )
    await create(
        USER,
        ticker="GGAL",
        name="Galicia ADR",
        instrument_type=InstrumentType.STOCK,
        market=Market.NASDAQ,
        currency=Currency.USD,
    )

    assert ggal.ticker == "GGAL"
    with pytest.raises(InstrumentTickerTakenError):
        await create(
            USER,
            ticker="Ggal",
            name="Otra",
            instrument_type=InstrumentType.CEDEAR,
            market=Market.BYMA,
            currency=Currency.ARS,
        )
    assert [i.market for i in await ListInstruments(uow=uow)()] == [Market.BYMA, Market.NASDAQ]


@pytest.mark.parametrize(
    ("instrument_type", "unit"),
    [(InstrumentType.BOND, 100), (InstrumentType.ON, 100), (InstrumentType.CEDEAR, 1)],
)
def test_bonds_and_ons_are_quoted_per_100_nominal(
    instrument_type: InstrumentType, unit: int
) -> None:
    instrument = Instrument(USER, "AL30", "Bonar 2030", instrument_type, Market.BYMA, Currency.ARS)
    assert instrument.quote_unit == unit


def test_ticker_and_name_are_required() -> None:
    with pytest.raises(InvalidInstrumentError):
        Instrument(USER, "  ", "Sin ticker", InstrumentType.ETF, Market.NYSE, Currency.USD)
