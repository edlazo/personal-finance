"""Pagos de deudas y cobros de préstamos: mueven plata de una cuenta de ledger."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID, uuid4

from app.modules.debts.domain.debt import CENTS, DebtInstallment
from app.shared.domain.errors import DomainError


class InvalidPaymentError(DomainError):
    pass


@dataclass
class DebtPayment:
    user_id: UUID
    debt_id: UUID
    account_id: UUID
    amount: Decimal
    date: date
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.amount <= 0 or self.amount != self.amount.quantize(CENTS):
            raise InvalidPaymentError("El pago tiene que ser mayor a cero y con hasta 2 decimales")


@dataclass(frozen=True)
class DebtBalance:
    paid: Decimal
    # Decisión del PO: lo que falta pagar, con el interés de las cuotas que quedan.
    pending: Decimal
    paid_installments: int
    next_installment: DebtInstallment | None

    @classmethod
    def of(cls, installments: list[DebtInstallment], paid: Decimal) -> DebtBalance:
        """Decisión del PO: lo pagado cubre las cuotas en orden; pagada es la cubierta entera."""
        left, covered = paid, 0
        for installment in installments:
            if left < installment.amount:
                break
            left -= installment.amount
            covered += 1
        total = sum((i.amount for i in installments), Decimal("0.00"))
        upcoming = installments[covered] if covered < len(installments) else None
        return cls(paid, total - paid, covered, upcoming)


class PaymentRepository(Protocol):
    async def add(self, payment: DebtPayment) -> None: ...

    async def paid(self) -> dict[UUID, Decimal]:
        """Lo pagado de cada deuda del usuario; las que no tienen pagos no aparecen."""
        ...
