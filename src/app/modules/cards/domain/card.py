"""Tarjetas de crédito."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
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


class CreditCardRepository(Protocol):
    async def add(self, card: CreditCard) -> None: ...

    async def list_cards(self) -> list[CreditCard]: ...

    async def get_card(self, card_id: UUID) -> CreditCard: ...
