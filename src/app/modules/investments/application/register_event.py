"""Caso de uso: registrar un dividendo, un cupón o una amortización."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.modules.investments.application.register_trade import TradesUnitOfWork, holding_of
from app.modules.investments.domain.event import EventKind, InstrumentEvent, check_event

LABELS = {
    EventKind.DIVIDEND: "Dividendo",
    EventKind.COUPON: "Cupón",
    EventKind.AMORTIZATION: "Amortización",
}


@dataclass(frozen=True)
class RegisterEvent:
    uow: TradesUnitOfWork

    async def __call__(
        self,
        user_id: UUID,
        *,
        account_id: UUID,
        instrument_id: UUID,
        kind: EventKind,
        amount: Decimal,
        on: date,
        nominal: Decimal | None = None,
    ) -> InstrumentEvent:
        event = InstrumentEvent(user_id, account_id, instrument_id, kind, amount, on, nominal)
        async with self.uow:
            account = await self.uow.cash.account(account_id)
            instrument = await self.uow.instruments.get_instrument(instrument_id)
            holding = await holding_of(self.uow, account_id, instrument_id)
            check_event(event, account, instrument, holding)
            await self.uow.events.add(event)
            description = f"{LABELS[kind]} {instrument.ticker}"
            if kind is EventKind.AMORTIZATION:
                # Devolución de capital: acredita la cuenta pero no es ingreso (decisión del PO).
                await self.uow.cash.record_trade(
                    account_id,
                    amount,
                    incoming=True,
                    on=on,
                    trade_id=event.id,
                    description=description,
                )
            else:
                await self.uow.cash.record_income(
                    account_id, amount, on=on, trade_id=event.id, description=description
                )
            await self.uow.commit()
        return event
