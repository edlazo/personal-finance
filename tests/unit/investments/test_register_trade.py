from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.modules.investments.application.register_trade import RegisterTrade
from app.modules.investments.domain.instrument import Instrument, InstrumentType, Market
from app.modules.investments.domain.trade import InvalidTradeError, TradeSide
from app.shared.domain.cash import CashAccount
from app.shared.domain.errors import DomainError
from app.shared.domain.money import Currency
from fakes.investments import FakeCash, FakeInvestmentsUnitOfWork

USER = uuid4()
BUY, SELL = TradeSide.BUY, TradeSide.SELL


def setup() -> tuple[FakeInvestmentsUnitOfWork, CashAccount, Instrument, Instrument]:
    uow = FakeInvestmentsUnitOfWork()
    broker = CashAccount(uuid4(), Currency.ARS, holds_investments=True, archived=False)
    uow.cash.accounts[broker.id] = broker
    ggal = Instrument(USER, "GGAL", "Galicia", InstrumentType.STOCK, Market.BYMA, Currency.ARS)
    al30 = Instrument(USER, "AL30", "Bonar 2030", InstrumentType.BOND, Market.BYMA, Currency.ARS)
    uow.instruments.items += [ggal, al30]
    return uow, broker, ggal, al30


async def trade(
    uow: FakeInvestmentsUnitOfWork,
    account: CashAccount,
    instrument: Instrument,
    side: TradeSide,
    quantity: str,
    price: str,
    fee: str = "0",
) -> Decimal:
    _, cash = await RegisterTrade(uow=uow)(
        USER,
        account_id=account.id,
        instrument_id=instrument.id,
        side=side,
        quantity=Decimal(quantity),
        price=Decimal(price),
        fee=Decimal(fee),
        on=date(2026, 10, 24),
    )
    return cash


async def test_buy_debits_price_times_quantity_plus_fee_and_sell_credits_minus_fee() -> None:
    uow, broker, ggal, al30 = setup()

    bought = await trade(uow, broker, ggal, BUY, "10", "6500.5", fee="100")
    bond = await trade(uow, broker, al30, BUY, "1000", "75000")  # cada 100 VN
    sold = await trade(uow, broker, ggal, SELL, "4", "7000", fee="50")

    assert (bought, bond, sold) == (Decimal("65105.00"), Decimal("750000.00"), Decimal("27950.00"))
    assert [incoming for _, _, incoming in uow.cash.recorded] == [False, False, True]
    assert uow.commits == 3


async def test_trade_rules() -> None:
    uow, broker, ggal, _ = setup()
    await trade(uow, broker, ggal, BUY, "5", "100")
    savings = CashAccount(uuid4(), Currency.ARS, holds_investments=False, archived=False)
    dollars = CashAccount(uuid4(), Currency.USD, holds_investments=True, archived=False)
    uow.cash.accounts.update({savings.id: savings, dollars.id: dollars})

    with pytest.raises(InvalidTradeError, match="vender más"):
        await trade(uow, broker, ggal, SELL, "6", "100")
    with pytest.raises(InvalidTradeError, match="comitente"):
        await trade(uow, savings, ggal, BUY, "1", "100")
    with pytest.raises(InvalidTradeError, match="moneda"):
        await trade(uow, dollars, ggal, BUY, "1", "100")
    with pytest.raises(InvalidTradeError, match="comisión"):
        await trade(uow, broker, ggal, SELL, "1", "10", fee="10")
    with pytest.raises(InvalidTradeError, match="cantidad"):
        await trade(uow, broker, ggal, BUY, "0.000000001", "100")
    with pytest.raises(InvalidTradeError, match="negativa"):
        await trade(uow, broker, ggal, BUY, "1", "100", fee="-1")
    closed = CashAccount(uuid4(), Currency.ARS, holds_investments=True, archived=True)
    uow.cash.accounts[closed.id] = closed
    with pytest.raises(InvalidTradeError, match="archivada"):
        await trade(uow, closed, ggal, BUY, "1", "100")
    assert len(uow.trades.items) == 1


class RejectingCash(FakeCash):
    """Como ledger cuando el movimiento dejaría la cuenta en negativo."""

    async def record_trade(
        self,
        account_id: UUID,
        amount: Decimal,
        *,
        incoming: bool,
        on: date,
        trade_id: UUID,
        description: str,
    ) -> None:
        raise DomainError("La cuenta quedaría con saldo negativo")


async def test_a_trade_whose_cash_movement_fails_is_not_kept() -> None:
    uow, broker, ggal, _ = setup()
    uow.cash = RejectingCash()
    uow.cash.accounts[broker.id] = broker

    with pytest.raises(DomainError):
        await trade(uow, broker, ggal, BUY, "10", "6500")

    assert await uow.trades.list_trades() == []
