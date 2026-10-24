"""Cuenta y sus reglas."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from app.shared.domain.errors import ConflictError, DomainError
from app.shared.domain.money import Currency

CENTS = Decimal("0.01")


class AccountType(StrEnum):
    SAVINGS = "SAVINGS"
    CASH = "CASH"
    WALLET = "WALLET"
    BROKER = "BROKER"
    CRYPTO_WALLET = "CRYPTO_WALLET"


# Decisión del PO: solo la comitente puede quedar en negativo (margen, caución tomadora).
ALLOWS_NEGATIVE_BALANCE = frozenset({AccountType.BROKER})


class InvalidAccountError(DomainError):
    pass


class AccountNameTakenError(ConflictError):
    def __init__(self) -> None:
        super().__init__("Ya tenés una cuenta activa con ese nombre")


class AccountArchivedError(ConflictError):
    def __init__(self) -> None:
        super().__init__("La cuenta está archivada y no se puede editar")


def same_name(name: str) -> str:
    """Forma de comparar nombres: sin espacios sobrantes ni distinguir mayúsculas.

    Usa lower() y no casefold() para coincidir con el lower() del índice de Postgres.
    """
    return name.strip().lower()


@dataclass
class Account:
    user_id: UUID
    name: str
    type: AccountType
    currency: Currency
    initial_balance: Decimal
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    archived_at: datetime | None = None

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if self.initial_balance != self.initial_balance.quantize(CENTS):
            raise InvalidAccountError("El saldo inicial admite hasta 2 decimales")
        if self.initial_balance < 0 and self.type not in ALLOWS_NEGATIVE_BALANCE:
            raise InvalidAccountError("Este tipo de cuenta no admite saldo negativo")

    def edit(self, *, name: str | None = None, currency: Currency | None = None) -> None:
        # Decisión del PO: las archivadas son de solo lectura.
        if self.archived_at is not None:
            raise AccountArchivedError
        if name is not None:
            self.name = name.strip()
        if currency is not None:
            self.currency = currency

    def archive(self) -> None:
        """Idempotente: archivar una cuenta ya archivada no cambia nada."""
        if self.archived_at is None:
            self.archived_at = datetime.now(UTC)


class AccountRepository(Protocol):
    """Repositorio de las cuentas de un usuario (ya filtrado por su dueño)."""

    async def name_taken(self, name: str, *, excluding: UUID | None = None) -> bool:
        """Hay otra cuenta activa con ese nombre (comparado con `same_name`)."""
        ...

    async def add(self, account: Account) -> None: ...

    async def get_account(self, account_id: UUID) -> Account:
        """NotFoundError si no existe o es de otro usuario."""
        ...

    async def list_accounts(self, *, include_archived: bool) -> list[Account]: ...

    async def save(self, account: Account) -> None: ...
