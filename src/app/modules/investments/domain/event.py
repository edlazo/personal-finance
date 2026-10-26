"""Dividendos, cupones y amortizaciones de un instrumento en una cuenta."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from app.modules.investments.domain.instrument import Instrument, InstrumentType
from app.modules.investments.domain.trade import (
    CENTS,
    QUANTITY_PRECISION,
    InvalidTradeError,
    check_account,
)
from app.shared.domain.cash import CashAccount


class EventKind(StrEnum):
    DIVIDEND = "DIVIDEND"
    COUPON = "COUPON"
    AMORTIZATION = "AMORTIZATION"


# Dividendos para acciones, CEDEARs y ETFs; cupones y amortizaciones para bonos y ONs.
ALLOWED = {
    EventKind.DIVIDEND: {InstrumentType.STOCK, InstrumentType.CEDEAR, InstrumentType.ETF},
    EventKind.COUPON: {InstrumentType.BOND, InstrumentType.ON},
    EventKind.AMORTIZATION: {InstrumentType.BOND, InstrumentType.ON},
}


@dataclass
class InstrumentEvent:
    """`amount` es lo cobrado; en una amortización, `nominal` es el VN que se devolvió."""

    user_id: UUID
    account_id: UUID
    instrument_id: UUID
    kind: EventKind
    amount: Decimal
    date: date
    nominal: Decimal | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.amount <= 0 or self.amount != self.amount.quantize(CENTS):
            raise InvalidTradeError("Lo cobrado tiene que ser mayor a cero y con 2 decimales")
        amortizes = self.kind is EventKind.AMORTIZATION
        if amortizes != (self.nominal is not None):
            raise InvalidTradeError("El valor nominal se indica solo en las amortizaciones")
        nominal = self.nominal
        if nominal is not None and (
            nominal <= 0 or nominal != nominal.quantize(QUANTITY_PRECISION)
        ):
            raise InvalidTradeError("El valor nominal amortizado tiene que ser mayor a cero")


def check_event(
    event: InstrumentEvent, account: CashAccount, instrument: Instrument, holding: Decimal
) -> None:
    check_account(account, instrument)
    if instrument.type not in ALLOWED[event.kind]:
        raise InvalidTradeError(f"{instrument.ticker} no admite eventos {event.kind}")
    if holding <= 0:
        raise InvalidTradeError("No tenés ese instrumento en esta cuenta")
    if event.nominal is not None and event.nominal > holding:
        raise InvalidTradeError(f"No se puede amortizar más de lo que tenés ({holding})")


class EventRepository(Protocol):
    async def add(self, event: InstrumentEvent) -> None: ...

    async def list_events(self) -> list[InstrumentEvent]: ...

    async def amortized(self, account_id: UUID, instrument_id: UUID) -> Decimal:
        """VN ya amortizado del instrumento en esa cuenta: se descuenta de la tenencia."""
        ...
