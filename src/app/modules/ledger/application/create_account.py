"""Caso de uso: crear una cuenta."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.modules.ledger.domain.account import (
    Account,
    AccountNameTakenError,
    AccountRepository,
    AccountType,
)
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.money import Currency


class AccountsUnitOfWork(UnitOfWork, Protocol):
    @property
    def accounts(self) -> AccountRepository: ...


@dataclass(frozen=True)
class CreateAccount:
    uow: AccountsUnitOfWork

    async def __call__(
        self,
        *,
        user_id: UUID,
        name: str,
        account_type: AccountType,
        currency: Currency,
        initial_balance: Decimal,
    ) -> Account:
        account = Account(
            user_id=user_id,
            name=name,
            type=account_type,
            currency=currency,
            initial_balance=initial_balance,
        )
        async with self.uow:
            if await self.uow.accounts.name_taken(account.name):
                raise AccountNameTakenError
            await self.uow.accounts.add(account)
            await self.uow.commit()
        return account
