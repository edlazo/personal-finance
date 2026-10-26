from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.investments.application.register_event import RegisterEvent
from app.modules.investments.application.register_trade import RegisterTrade
from app.modules.investments.domain.event import EventKind, InstrumentEvent
from app.modules.investments.domain.instrument import Instrument, InstrumentType, Market
from app.modules.investments.domain.position import build_positions
from app.modules.investments.domain.trade import InvalidTradeError, Trade, TradeSide
from app.shared.domain.cash import CashAccount
from app.shared.domain.money import Currency
from fakes.investments import FakeInvestmentsUnitOfWork

USER = uuid4()
DAY = date(2026, 10, 24)
GGAL = Instrument(USER, "GGAL", "Galicia", InstrumentType.STOCK, Market.BYMA, Currency.ARS)
AL30 = Instrument(USER, "AL30", "Bonar 2030", InstrumentType.BOND, Market.BYMA, Currency.ARS)


async def setup() -> tuple[FakeInvestmentsUnitOfWork, CashAccount]:
    uow = FakeInvestmentsUnitOfWork()
    broker = CashAccount(uuid4(), Currency.ARS, holds_investments=True, archived=False)
    uow.cash.accounts[broker.id] = broker
    uow.instruments.items += [GGAL, AL30]
    for instrument, quantity, price in ((GGAL, "10", "100"), (AL30, "1000", "75000")):
        buy = Trade(
            USER,
            broker.id,
            instrument.id,
            TradeSide.BUY,
            Decimal(quantity),
            Decimal(price),
            Decimal("0"),
            DAY,
        )
        uow.trades.items.append(buy)
    return uow, broker


async def event(
    uow: FakeInvestmentsUnitOfWork,
    broker: CashAccount,
    instrument: Instrument,
    kind: EventKind,
    amount: str,
    nominal: str | None = None,
) -> InstrumentEvent:
    return await RegisterEvent(uow=uow)(
        USER,
        account_id=broker.id,
        instrument_id=instrument.id,
        kind=kind,
        amount=Decimal(amount),
        on=DAY,
        nominal=None if nominal is None else Decimal(nominal),
    )


async def test_dividends_and_coupons_are_income_and_amortizations_return_capital() -> None:
    uow, broker = await setup()

    await event(uow, broker, GGAL, EventKind.DIVIDEND, "250.00")
    await event(uow, broker, AL30, EventKind.COUPON, "5000.00")
    await event(uow, broker, AL30, EventKind.AMORTIZATION, "200000.00", nominal="250")

    assert uow.cash.incomes == [(broker.id, Decimal("250.00")), (broker.id, Decimal("5000.00"))]
    assert uow.cash.recorded[-1] == (broker.id, Decimal("200000.00"), True)
    with pytest.raises(InvalidTradeError, match="vender más"):
        await RegisterTrade(uow=uow)(
            USER,
            account_id=broker.id,
            instrument_id=AL30.id,
            side=TradeSide.SELL,
            quantity=Decimal("751"),
            price=Decimal("75000"),
            fee=Decimal("0"),
            on=DAY,
        )


async def test_event_rules() -> None:
    uow, broker = await setup()
    elsewhere = CashAccount(uuid4(), Currency.ARS, holds_investments=True, archived=False)
    uow.cash.accounts[elsewhere.id] = elsewhere

    with pytest.raises(InvalidTradeError, match="no admite"):
        await event(uow, broker, GGAL, EventKind.COUPON, "1.00")
    with pytest.raises(InvalidTradeError, match="No tenés"):
        await event(uow, elsewhere, GGAL, EventKind.DIVIDEND, "1.00")
    with pytest.raises(InvalidTradeError, match="amortizar más"):
        await event(uow, broker, AL30, EventKind.AMORTIZATION, "1.00", nominal="1001")
    with pytest.raises(InvalidTradeError, match="solo en las amortizaciones"):
        await event(uow, broker, GGAL, EventKind.DIVIDEND, "1.00", nominal="1")
    with pytest.raises(InvalidTradeError, match="mayor a cero"):
        await event(uow, broker, GGAL, EventKind.DIVIDEND, "0")
    assert uow.events.items == []


async def test_positions_add_income_and_treat_amortization_as_a_partial_redemption() -> None:
    uow, broker = await setup()
    await event(uow, broker, AL30, EventKind.COUPON, "5000.00")
    await event(uow, broker, AL30, EventKind.AMORTIZATION, "200000.00", nominal="250")

    instruments = {i.id: i for i in uow.instruments.items}
    events = await uow.events.list_events()
    by_ticker = {
        p.instrument.ticker: p for p in build_positions(uow.trades.items, instruments, None, events)
    }

    bond = by_ticker["AL30"]
    # Costo 750.000 por 1.000 VN: salen 250 VN a costo 187.500 y se cobran 200.000.
    assert (bond.quantity, bond.cost) == (Decimal("750"), Decimal("562500.00"))
    assert bond.realized_pnl == Decimal("17500.00")
