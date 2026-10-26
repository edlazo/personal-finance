"""Compra y venta de instrumentos desde una cuenta comitente o wallet."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from app.modules.investments.domain.instrument import Instrument
from app.shared.domain.cash import CashAccount
from app.shared.domain.errors import DomainError

CENTS = Decimal("0.01")
# Cripto se opera en fracciones; los precios, con la precisión de las cotizaciones.
QUANTITY_PRECISION = Decimal("1e-8")
PRICE_PRECISION = Decimal("1e-10")


class TradeSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class InvalidTradeError(DomainError):
    pass


@dataclass
class Trade:
    user_id: UUID
    account_id: UUID
    instrument_id: UUID
    side: TradeSide
    quantity: Decimal
    price: Decimal
    fee: Decimal
    date: date
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        for value, precision, name in (
            (self.quantity, QUANTITY_PRECISION, "La cantidad"),
            (self.price, PRICE_PRECISION, "El precio"),
        ):
            if value <= 0 or value != value.quantize(precision):
                raise InvalidTradeError(f"{name} tiene que ser mayor a cero y con menos decimales")
        if self.fee < 0 or self.fee != self.fee.quantize(CENTS):
            raise InvalidTradeError("La comisión no puede ser negativa y admite 2 decimales")

    def cash(self, quote_unit: int) -> Decimal:
        """Lo que sale de la cuenta (compra) o entra (venta): precio x cantidad / unidad de
        cotización (100 en bonos y ONs), más la comisión en la compra y menos en la venta."""
        gross = (self.price * self.quantity / quote_unit).quantize(CENTS, ROUND_HALF_UP)
        cash = gross + self.fee if self.side is TradeSide.BUY else gross - self.fee
        if cash <= 0:
            raise InvalidTradeError("La comisión no puede ser mayor que el monto de la venta")
        return cash


def check_account(account: CashAccount, instrument: Instrument) -> None:
    if not account.holds_investments:
        raise InvalidTradeError("Se opera desde una cuenta comitente o una wallet cripto")
    if account.archived:
        raise InvalidTradeError("No se pueden cargar operaciones en una cuenta archivada")
    if account.currency is not instrument.currency:
        raise InvalidTradeError("La cuenta tiene que estar en la moneda del instrumento")


def check_trade(
    trade: Trade, account: CashAccount, instrument: Instrument, holding: Decimal
) -> None:
    """Decisiones del PO: misma moneda que el instrumento y tenencia por cuenta."""
    check_account(account, instrument)
    if trade.side is TradeSide.SELL and trade.quantity > holding:
        raise InvalidTradeError(f"No podés vender más de lo que tenés en esta cuenta ({holding})")


class TradeRepository(Protocol):
    async def add(self, trade: Trade) -> None: ...

    async def holding(self, account_id: UUID, instrument_id: UUID) -> Decimal:
        """Compras menos ventas del instrumento en esa cuenta."""
        ...

    async def list_trades(self) -> list[Trade]: ...
