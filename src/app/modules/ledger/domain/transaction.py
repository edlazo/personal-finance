"""Movimientos: ingresos, gastos y transferencias entre cuentas."""

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
    """El monto siempre es positivo; `kind` define si suma (ingreso) o resta (gasto).

    Una transferencia son dos movimientos sin categoría ligados por `transfer_group_id`.
    """

    user_id: UUID
    account_id: UUID
    kind: CategoryKind
    amount: Decimal
    date: date
    category_id: UUID | None
    description: str | None = None
    transfer_group_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise InvalidTransactionError("El monto tiene que ser mayor a cero")
        if self.amount != self.amount.quantize(CENTS):
            raise InvalidTransactionError("El monto admite hasta 2 decimales")
        if (self.category_id is None) == (self.transfer_group_id is None):
            raise InvalidTransactionError("Un movimiento lleva categoría o es una transferencia")
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


@dataclass(frozen=True)
class Transfer:
    group_id: UUID
    outgoing: Transaction
    incoming: Transaction


def transfer(
    user_id: UUID,
    source: Account,
    target: Account,
    amount: Decimal,
    on: date,
    description: str | None = None,
) -> Transfer:
    """Gasto en el origen e ingreso en el destino; no cuentan en los reportes (US-019)."""
    if source.id == target.id:
        raise InvalidTransactionError("El origen y el destino tienen que ser cuentas distintas")
    if source.currency is not target.currency:
        raise InvalidTransactionError("Las cuentas tienen que ser de la misma moneda")
    if source.archived_at is not None or target.archived_at is not None:
        raise InvalidTransactionError("No se pueden cargar movimientos en una cuenta archivada")
    group = uuid4()

    def leg(account: Account, kind: CategoryKind) -> Transaction:
        return Transaction(
            user_id, account.id, kind, amount, on, None, description, transfer_group_id=group
        )

    return Transfer(group, leg(source, CategoryKind.EXPENSE), leg(target, CategoryKind.INCOME))


class TransactionRepository(Protocol):
    async def add(self, transaction: Transaction) -> None: ...

    async def search(
        self, filters: TransactionFilter, *, limit: int, offset: int
    ) -> tuple[list[Transaction], int]:
        """Página ordenada por fecha descendente y el total de coincidencias."""
        ...
