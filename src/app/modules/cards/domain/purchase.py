"""Compras con tarjeta, en una o más cuotas."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import ROUND_DOWN, Decimal
from typing import Protocol
from uuid import UUID, uuid4

from app.modules.cards.domain.card import CENTS, CreditCard
from app.shared.domain.errors import DomainError
from app.shared.domain.money import Currency

MAX_INSTALLMENTS = 60


class InvalidPurchaseError(DomainError):
    pass


@dataclass(frozen=True)
class Installment:
    purchase_id: UUID
    description: str
    number: int
    count: int
    amount: Decimal
    currency: Currency
    closing_date: date
    due_date: date


@dataclass
class CardPurchase:
    user_id: UUID
    card_id: UUID
    description: str
    # Lo que se paga en total, en la moneda de la compra.
    amount: Decimal
    currency: Currency
    installments: int
    date: date
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.description = self.description.strip()
        if not self.description:
            raise InvalidPurchaseError("La descripción es obligatoria")
        if self.amount <= 0 or self.amount != self.amount.quantize(CENTS):
            raise InvalidPurchaseError(
                "El monto tiene que ser mayor a cero y con hasta 2 decimales"
            )
        if not 1 <= self.installments <= MAX_INSTALLMENTS:
            raise InvalidPurchaseError(f"Las cuotas van de 1 a {MAX_INSTALLMENTS}")
        if self.amount / self.installments < CENTS:
            raise InvalidPurchaseError("El monto no alcanza para esa cantidad de cuotas")

    def schedule(self, card: CreditCard) -> list[Installment]:
        """Una cuota por resumen desde el que incluye la fecha de compra. Decisión del PO: los
        centavos que sobran van en la primera, así la suma da el total exacto."""
        if self.currency not in card.currencies:
            raise InvalidPurchaseError("La tarjeta no es bimonetaria: solo acepta compras en pesos")
        rest = (self.amount / self.installments).quantize(CENTS, ROUND_DOWN)
        first = self.amount - rest * (self.installments - 1)
        return [
            Installment(
                self.id,
                self.description,
                number,
                self.installments,
                first if number == 1 else rest,
                self.currency,
                *card.statement(self.date, number - 1),
            )
            for number in range(1, self.installments + 1)
        ]


class PurchaseRepository(Protocol):
    async def add(self, purchase: CardPurchase, installments: list[Installment]) -> None: ...

    async def pending_installments(self, card_id: UUID, today: date) -> list[Installment]:
        """Decisión del PO: las cuotas de resúmenes que todavía no vencieron."""
        ...
