"""Caso de uso: registrar una compra o venta de un instrumento."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.modules.investments.application.manage_instruments import InvestmentsUnitOfWork
from app.modules.investments.domain.credentials import BrokerLinkRepository
from app.modules.investments.domain.event import EventRepository
from app.modules.investments.domain.trade import (
    InvalidTradeError,
    Trade,
    TradeRepository,
    TradeSide,
    check_trade,
)
from app.shared.domain.cash import CashMovements


class TradesUnitOfWork(InvestmentsUnitOfWork, Protocol):
    """La operación y el movimiento de la cuenta (ledger) van en la misma transacción."""

    @property
    def trades(self) -> TradeRepository: ...

    @property
    def events(self) -> EventRepository: ...

    @property
    def links(self) -> BrokerLinkRepository: ...

    @property
    def cash(self) -> CashMovements: ...


async def ensure_not_linked(uow: TradesUnitOfWork, account_id: UUID) -> None:
    """En la cuenta vinculada a un broker las tenencias vienen de su portafolio (PF-51)."""
    broker = await uow.links.broker_of(account_id)
    if broker is not None:
        raise InvalidTradeError(f"La cuenta está vinculada a {broker}: sus tenencias vienen de ahí")


async def holding_of(uow: TradesUnitOfWork, account_id: UUID, instrument_id: UUID) -> Decimal:
    """Compras menos ventas, menos el VN que ya se amortizó."""
    bought = await uow.trades.holding(account_id, instrument_id)
    return bought - await uow.events.amortized(account_id, instrument_id)


@dataclass(frozen=True)
class RegisterTrade:
    uow: TradesUnitOfWork

    async def __call__(
        self,
        user_id: UUID,
        *,
        account_id: UUID,
        instrument_id: UUID,
        side: TradeSide,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal,
        on: date,
    ) -> tuple[Trade, Decimal]:
        """Devuelve la operación y lo que movió en la cuenta."""
        trade = Trade(user_id, account_id, instrument_id, side, quantity, price, fee, on)
        async with self.uow:
            account = await self.uow.cash.account(account_id)
            instrument = await self.uow.instruments.get_instrument(instrument_id)
            await ensure_not_linked(self.uow, account_id)
            holding = await holding_of(self.uow, account_id, instrument_id)
            check_trade(trade, account, instrument, holding)
            cash = trade.cash(instrument.quote_unit)
            await self.uow.trades.add(trade)
            verb = "Compra" if side is TradeSide.BUY else "Venta"
            await self.uow.cash.record_trade(
                account_id,
                cash,
                incoming=side is TradeSide.SELL,
                on=on,
                trade_id=trade.id,
                description=f"{verb} {quantity.normalize()} {instrument.ticker}",
            )
            await self.uow.commit()
        return trade, cash
