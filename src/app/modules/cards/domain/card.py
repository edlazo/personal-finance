"""Tarjetas de crédito."""

from calendar import monthrange
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from app.shared.domain.errors import DomainError
from app.shared.domain.money import Currency

CENTS = Decimal("0.01")


class CardNetwork(StrEnum):
    VISA = "VISA"
    MASTERCARD = "MASTERCARD"
    AMEX = "AMEX"
    CABAL = "CABAL"
    NARANJA = "NARANJA"


class InvalidCardError(DomainError):
    pass


def _day(year: int, month: int, day: int) -> date:
    """Ese día del mes o, si el mes es más corto, su último día (decisión del PO)."""
    return date(year, month, min(day, monthrange(year, month)[1]))


def _shift(year: int, month: int, months: int) -> tuple[int, int]:
    year, index = divmod(year * 12 + month - 1 + months, 12)
    return year, index + 1


@dataclass
class CreditCard:
    """Decisiones del PO: el cierre y el vencimiento son un día fijo del mes (en un mes más corto,
    su último día); toda tarjeta tiene saldo en pesos y, si es bimonetaria, también en dólares."""

    user_id: UUID
    name: str
    network: CardNetwork
    closing_day: int
    due_day: int
    dual_currency: bool = False
    # En pesos: las compras en dólares también lo consumen.
    limit: Decimal | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise InvalidCardError("El nombre es obligatorio")
        if not (1 <= self.closing_day <= 31 and 1 <= self.due_day <= 31):
            raise InvalidCardError("El cierre y el vencimiento son días del mes, del 1 al 31")
        if self.limit is not None and (self.limit <= 0 or self.limit != self.limit.quantize(CENTS)):
            raise InvalidCardError("El límite tiene que ser mayor a cero y con hasta 2 decimales")

    @property
    def currencies(self) -> list[Currency]:
        return [Currency.ARS, Currency.USD] if self.dual_currency else [Currency.ARS]

    def statement(self, purchase_date: date, months_later: int = 0) -> tuple[date, date]:
        """Cierre y vencimiento del resumen que incluye esa fecha, o del de N meses después.
        Una compra del mismo día del cierre entra en ese resumen."""
        year, month = purchase_date.year, purchase_date.month
        if purchase_date > _day(year, month, self.closing_day):
            months_later += 1
        year, month = _shift(year, month, months_later)
        closing = _day(year, month, self.closing_day)
        # Un vencimiento anterior al cierre en el mes cae en el mes siguiente.
        due_year, due_month = (
            (year, month) if self.due_day > self.closing_day else _shift(year, month, 1)
        )
        return closing, _day(due_year, due_month, self.due_day)


class CreditCardRepository(Protocol):
    async def add(self, card: CreditCard) -> None: ...

    async def list_cards(self) -> list[CreditCard]: ...

    async def get_card(self, card_id: UUID) -> CreditCard: ...
