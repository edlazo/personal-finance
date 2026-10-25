"""Movimientos: ingresos, gastos y transferencias entre cuentas."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol
from uuid import UUID, uuid4

from app.modules.ledger.domain.account import CENTS, Account
from app.modules.ledger.domain.category import Category, CategoryKind
from app.shared.domain.errors import DomainError
from app.shared.domain.money import Currency


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


# Tipo de cambio efectivo: pesos por dólar, con 4 decimales.
RATE_PRECISION = Decimal("0.0001")


@dataclass(frozen=True)
class Transfer:
    group_id: UUID
    outgoing: Transaction
    incoming: Transaction
    # Solo en la compra o venta de dólares (US-020); sale de los dos montos guardados.
    exchange_rate: Decimal | None = None
    # Comisión: gasto aparte en el origen, no es una pata de la transferencia.
    fee: Transaction | None = None


def transfer(
    user_id: UUID,
    source: Account,
    target: Account,
    amount: Decimal,
    on: date,
    description: str | None = None,
    received: Decimal | None = None,
) -> Transfer:
    """Gasto en el origen e ingreso en el destino; no cuentan en los reportes (US-019).

    Entre monedas distintas (compra o venta de dólares) cada pata lleva su monto: `amount`
    sale del origen y `received` entra al destino.
    """
    if source.id == target.id:
        raise InvalidTransactionError("El origen y el destino tienen que ser cuentas distintas")
    if source.archived_at is not None or target.archived_at is not None:
        raise InvalidTransactionError("No se pueden cargar movimientos en una cuenta archivada")
    same_currency = source.currency is target.currency
    if same_currency and received not in (None, amount):
        raise InvalidTransactionError("En la misma moneda sale y entra el mismo monto")
    if not same_currency and received is None:
        raise InvalidTransactionError("Entre monedas distintas hace falta el monto que entra")
    group = uuid4()

    def leg(account: Account, kind: CategoryKind, value: Decimal) -> Transaction:
        return Transaction(
            user_id, account.id, kind, value, on, None, description, transfer_group_id=group
        )

    incoming = received if received is not None else amount
    rate = None
    if not same_currency:
        pesos, dollars = (
            (amount, incoming) if source.currency is Currency.ARS else (incoming, amount)
        )
        rate = (pesos / dollars).quantize(RATE_PRECISION, ROUND_HALF_UP)
    return Transfer(
        group,
        leg(source, CategoryKind.EXPENSE, amount),
        leg(target, CategoryKind.INCOME, incoming),
        rate,
    )


class TransactionRepository(Protocol):
    async def add(self, transaction: Transaction) -> None: ...

    async def search(
        self, filters: TransactionFilter, *, limit: int, offset: int
    ) -> tuple[list[Transaction], int]:
        """Página ordenada por fecha descendente y el total de coincidencias."""
        ...

    async def get_transaction(self, transaction_id: UUID) -> Transaction: ...

    async def transfer_legs(self, group_id: UUID) -> list[Transaction]: ...

    async def save(self, transaction: Transaction) -> None: ...

    async def delete(self, transaction_id: UUID) -> None: ...
