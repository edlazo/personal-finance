"""Caso de uso: registrar un ingreso o un gasto."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.modules.ledger.application.balance_guard import ensure_non_negative
from app.modules.ledger.application.list_categories import LedgerUnitOfWork
from app.modules.ledger.domain.account import AccountRepository
from app.modules.ledger.domain.category import CategoryKind
from app.modules.ledger.domain.transaction import (
    Transaction,
    TransactionRepository,
    check_movement,
)


class TransactionsUnitOfWork(LedgerUnitOfWork, Protocol):
    """Cuenta, categoría y movimiento en la misma transacción."""

    @property
    def accounts(self) -> AccountRepository: ...

    @property
    def transactions(self) -> TransactionRepository: ...


@dataclass(frozen=True)
class CreateTransaction:
    uow: TransactionsUnitOfWork

    async def __call__(
        self,
        user_id: UUID,
        *,
        account_id: UUID,
        kind: CategoryKind,
        amount: Decimal,
        on: date,
        category_id: UUID,
        description: str | None = None,
    ) -> Transaction:
        transaction = Transaction(
            user_id=user_id,
            account_id=account_id,
            kind=kind,
            amount=amount,
            date=on,
            category_id=category_id,
            description=description,
        )
        async with self.uow:
            account = await self.uow.accounts.get_account(account_id)
            category = await self.uow.categories.get_category(category_id)
            check_movement(kind, account, category)
            await self.uow.transactions.add(transaction)
            await ensure_non_negative(self.uow, {account_id: on})
            await self.uow.commit()
        return transaction
