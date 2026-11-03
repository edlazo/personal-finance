"""Reglas de movimientos recurrentes: la plantilla de un ingreso o gasto que se repite."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from app.modules.ledger.domain.account import CENTS
from app.modules.ledger.domain.category import CategoryKind
from app.modules.ledger.domain.transaction import Transaction
from app.shared.domain.dates import add_months
from app.shared.domain.errors import DomainError


class Frequency(StrEnum):
    # Decisión del PO: el día sale de la fecha de inicio (en un mes más corto, su último día).
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class InvalidRecurringError(DomainError):
    pass


@dataclass
class RecurringRule:
    """Decisión del PO: solo ingresos y gastos, con cuenta, categoría y monto fijo."""

    user_id: UUID
    account_id: UUID
    kind: CategoryKind
    amount: Decimal
    category_id: UUID
    frequency: Frequency
    start_date: date
    end_date: date | None = None
    description: str | None = None
    paused: bool = False
    # Decisión del PO: sus ocurrencias quedan pendientes, fuera del saldo, hasta confirmarlas.
    needs_confirmation: bool = False
    # Último día ya procesado por el job: lo anterior no se vuelve a generar.
    generated_until: date | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.amount <= 0 or self.amount != self.amount.quantize(CENTS):
            raise InvalidRecurringError(
                "El monto tiene que ser mayor a cero y con hasta 2 decimales"
            )
        if self.end_date is not None and self.end_date < self.start_date:
            raise InvalidRecurringError("La fecha de fin no puede ser anterior a la de inicio")
        self.description = (self.description or "").strip() or None

    def occurrence(self, n: int) -> date:
        """La ocurrencia número n, contando desde la fecha de inicio (la 0)."""
        if self.frequency is Frequency.WEEKLY:
            return self.start_date + timedelta(weeks=n)
        return add_months(self.start_date, n * (12 if self.frequency is Frequency.YEARLY else 1))

    def due_dates(self, today: date) -> list[date]:
        """Decisión del PO: todas las vencidas que falten, desde la fecha de inicio."""
        last = min(today, self.end_date or today)
        done = self.generated_until or date.min
        dates, n = [], 0
        while (day := self.occurrence(n)) <= last:
            if day > done:
                dates.append(day)
            n += 1
        return dates

    def movement(self, on: date, amount: Decimal | None = None) -> Transaction:
        return Transaction(
            self.user_id,
            self.account_id,
            self.kind,
            self.amount if amount is None else amount,
            on,
            self.category_id,
            self.description,
        )


@dataclass(frozen=True)
class PendingOccurrence:
    """Una ocurrencia de una regla con confirmación: no es un movimiento hasta confirmarla."""

    user_id: UUID
    rule_id: UUID
    date: date
    amount: Decimal
    id: UUID = field(default_factory=uuid4)


class RecurringRuleRepository(Protocol):
    async def add(self, rule: RecurringRule) -> None: ...

    async def list_rules(self) -> list[RecurringRule]: ...

    async def get_rule(self, rule_id: UUID) -> RecurringRule: ...

    async def save(self, rule: RecurringRule) -> None: ...

    async def delete(self, rule_id: UUID) -> None: ...

    async def advance(self, rule: RecurringRule, until: date) -> bool:
        """Mueve `generated_until` solo si nadie lo movió desde que se leyó la regla."""
        ...

    async def add_pending(self, pending: PendingOccurrence) -> None: ...

    async def list_pending(self) -> list[PendingOccurrence]: ...

    async def get_pending(self, pending_id: UUID) -> PendingOccurrence: ...

    async def delete_pending(self, pending_id: UUID) -> None: ...
