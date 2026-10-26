from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.investments.application.manage_credentials import LinkAccount
from app.modules.investments.application.register_event import RegisterEvent
from app.modules.investments.application.register_trade import RegisterTrade
from app.modules.investments.domain.credentials import Broker, InvalidCredentialsError
from app.modules.investments.domain.event import EventKind
from app.modules.investments.domain.instrument import Instrument, InstrumentType, Market
from app.modules.investments.domain.trade import InvalidTradeError, TradeSide
from app.shared.domain.cash import CashAccount
from app.shared.domain.errors import NotFoundError
from app.shared.domain.money import Currency
from fakes.investments import FakeInvestmentsUnitOfWork

USER = uuid4()
GGAL = Instrument(USER, "GGAL", "Galicia", InstrumentType.STOCK, Market.BYMA, Currency.ARS)


async def test_a_linked_account_takes_no_manual_trades_or_events() -> None:
    uow = FakeInvestmentsUnitOfWork()
    iol = CashAccount(uuid4(), Currency.ARS, holds_investments=True, archived=False)
    uow.cash.accounts[iol.id] = iol
    uow.instruments.items.append(GGAL)

    await LinkAccount(uow)(USER, Broker.IOL, iol.id)

    assert await uow.links.linked_account(Broker.IOL) == iol.id
    with pytest.raises(InvalidTradeError, match="vinculada a IOL"):
        await RegisterTrade(uow=uow)(
            USER,
            account_id=iol.id,
            instrument_id=GGAL.id,
            side=TradeSide.BUY,
            quantity=Decimal("1"),
            price=Decimal("1"),
            fee=Decimal("0"),
            on=date(2026, 10, 26),
        )
    with pytest.raises(InvalidTradeError, match="vinculada a IOL"):
        await RegisterEvent(uow=uow)(
            USER,
            account_id=iol.id,
            instrument_id=GGAL.id,
            kind=EventKind.DIVIDEND,
            amount=Decimal("1.00"),
            on=date(2026, 10, 26),
        )


async def test_only_an_active_investment_account_can_be_linked() -> None:
    uow = FakeInvestmentsUnitOfWork()
    savings = CashAccount(uuid4(), Currency.ARS, holds_investments=False, archived=False)
    closed = CashAccount(uuid4(), Currency.ARS, holds_investments=True, archived=True)
    uow.cash.accounts.update({savings.id: savings, closed.id: closed})

    for account in (savings, closed):
        with pytest.raises(InvalidCredentialsError, match="comitente activa"):
            await LinkAccount(uow)(USER, Broker.IOL, account.id)
    with pytest.raises(NotFoundError):
        await LinkAccount(uow)(USER, Broker.IOL, uuid4())
