"""Pagos de resúmenes: salen de una cuenta de ledger en la moneda que se paga."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID, uuid4

from app.modules.cards.domain.card import CENTS
from app.shared.domain.errors import DomainError
from app.shared.domain.money import Currency


class InvalidPaymentError(DomainError):
    pass


@dataclass
class CardPayment:
    user_id: UUID
    card_id: UUID
    account_id: UUID
    # El resumen que se paga, por su fecha de cierre.
    closing_date: date
    amount: Decimal
    currency: Currency
    date: date
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.amount <= 0 or self.amount != self.amount.quantize(CENTS):
            raise InvalidPaymentError("El pago tiene que ser mayor a cero y con hasta 2 decimales")


class PaymentRepository(Protocol):
    async def add(self, payment: CardPayment) -> None: ...

    async def paid(self, card_id: UUID) -> dict[tuple[date, Currency], Decimal]:
        """Lo pagado de cada resumen (por fecha de cierre) en cada moneda."""
        ...
