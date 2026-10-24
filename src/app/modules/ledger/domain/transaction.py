"""Movimientos: ingresos y gastos de una cuenta."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID, uuid4

from app.modules.ledger.domain.account import CENTS, Account
from app.modules.ledger.domain.category import Category, CategoryKind
from app.shared.domain.errors import DomainError


class InvalidTransactionError(DomainError):
    pass


@dataclass
class Transaction:
    """El monto siempre es positivo; `kind` define si suma (ingreso) o resta (gasto)."""

    user_id: UUID
    account_id: UUID
    kind: CategoryKind
    amount: Decimal
    date: date
    category_id: UUID
    description: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise InvalidTransactionError("El monto tiene que ser mayor a cero")
        if self.amount != self.amount.quantize(CENTS):
            raise InvalidTransactionError("El monto admite hasta 2 decimales")
        self.description = (self.description or "").strip() or None


def check_movement(kind: CategoryKind, account: Account, category: Category) -> None:
    """Reglas para cargar un movimiento en una cuenta con una categoría."""
    if account.archived_at is not None:
        raise InvalidTransactionError("No se pueden cargar movimientos en una cuenta archivada")
    if category.archived_at is not None:
        raise InvalidTransactionError("La categoría está archivada")
    if category.kind is not kind:
        raise InvalidTransactionError("La categoría no coincide con el tipo del movimiento")


@dataclass(frozen=True)
class TransactionFilter:
    """Filtros del listado; los que quedan en None no filtran."""

    date_from: date | None = None
    date_to: date | None = None
    account_id: UUID | None = None
    category_ids: frozenset[UUID] | None = None
    kind: CategoryKind | None = None
    text: str | None = None
    amount_min: Decimal | None = None
    amount_max: Decimal | None = None


class TransactionRepository(Protocol):
    async def add(self, transaction: Transaction) -> None: ...

    async def search(
        self, filters: TransactionFilter, *, limit: int, offset: int
    ) -> tuple[list[Transaction], int]:
        """Página ordenada por fecha descendente y el total de coincidencias."""
        ...
