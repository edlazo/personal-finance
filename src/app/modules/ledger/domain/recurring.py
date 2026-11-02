"""Reglas de movimientos recurrentes: la plantilla de un ingreso o gasto que se repite."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from app.modules.ledger.domain.account import CENTS
from app.modules.ledger.domain.category import CategoryKind
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


class RecurringRuleRepository(Protocol):
    async def add(self, rule: RecurringRule) -> None: ...

    async def list_rules(self) -> list[RecurringRule]: ...

    async def get_rule(self, rule_id: UUID) -> RecurringRule: ...

    async def save(self, rule: RecurringRule) -> None: ...

    async def delete(self, rule_id: UUID) -> None: ...
