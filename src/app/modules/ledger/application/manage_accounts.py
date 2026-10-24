"""Casos de uso: listar, editar y archivar cuentas."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.modules.ledger.application.create_account import AccountsUnitOfWork
from app.modules.ledger.domain.account import (
    Account,
    AccountCurrencyLockedError,
    AccountNameTakenError,
)
from app.shared.domain.money import Currency


@dataclass(frozen=True)
class AccountBalance:
    account: Account
    balance: Decimal


async def _with_balances(
    uow: AccountsUnitOfWork, accounts: list[Account], as_of: date | None
) -> list[AccountBalance]:
    # El saldo no se guarda: es el inicial más los movimientos (US-013).
    totals = await uow.accounts.movement_totals([a.id for a in accounts], as_of=as_of)
    return [AccountBalance(a, a.initial_balance + totals.get(a.id, Decimal("0"))) for a in accounts]


@dataclass(frozen=True)
class ListAccounts:
    uow: AccountsUnitOfWork

    async def __call__(
        self, *, include_archived: bool = False, as_of: date | None = None
    ) -> list[AccountBalance]:
        async with self.uow:
            accounts = await self.uow.accounts.list_accounts(include_archived=include_archived)
            return await _with_balances(self.uow, accounts, as_of)


@dataclass(frozen=True)
class GetAccount:
    uow: AccountsUnitOfWork

    async def __call__(self, account_id: UUID, *, as_of: date | None = None) -> AccountBalance:
        async with self.uow:
            account = await self.uow.accounts.get_account(account_id)
            [with_balance] = await _with_balances(self.uow, [account], as_of)
            return with_balance


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
