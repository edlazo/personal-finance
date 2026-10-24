"""Casos de uso: listar, editar y archivar cuentas."""

from dataclasses import dataclass
from uuid import UUID

from app.modules.ledger.application.create_account import AccountsUnitOfWork
from app.modules.ledger.domain.account import (
    Account,
    AccountCurrencyLockedError,
    AccountNameTakenError,
)
from app.shared.domain.money import Currency


@dataclass(frozen=True)
class ListAccounts:
    uow: AccountsUnitOfWork

    async def __call__(self, *, include_archived: bool = False) -> list[Account]:
        async with self.uow:
            return await self.uow.accounts.list_accounts(include_archived=include_archived)


@dataclass(frozen=True)
class UpdateAccount:
    uow: AccountsUnitOfWork

    async def __call__(
        self, account_id: UUID, *, name: str | None = None, currency: Currency | None = None
    ) -> Account:
        async with self.uow:
            account = await self.uow.accounts.get_account(account_id)
            currency_changes = currency is not None and currency != account.currency
            if currency_changes and await self.uow.accounts.has_movements(account.id):
                raise AccountCurrencyLockedError
            account.edit(name=name, currency=currency)
            # Excluye la propia cuenta: cambiar "galicia" por "Galicia" es válido.
            if name is not None and await self.uow.accounts.name_taken(
                account.name, excluding=account.id
            ):
                raise AccountNameTakenError
            await self.uow.accounts.save(account)
            await self.uow.commit()
        return account


@dataclass(frozen=True)
class ArchiveAccount:
    uow: AccountsUnitOfWork

    async def __call__(self, account_id: UUID) -> None:
        async with self.uow:
            account = await self.uow.accounts.get_account(account_id)
            account.archive()
            await self.uow.accounts.save(account)
            await self.uow.commit()
