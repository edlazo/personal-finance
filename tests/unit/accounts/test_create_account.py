from decimal import Decimal
from types import TracebackType
from typing import Self
from uuid import uuid4

import pytest

from app.modules.accounts.application.create_account import CreateAccount
from app.modules.accounts.domain.account import (
    Account,
    AccountNameTakenError,
    AccountType,
    InvalidAccountError,
    same_name,
)
from app.shared.domain.money import Currency

USER = uuid4()


class InMemoryAccounts:
    def __init__(self) -> None:
        self.items: list[Account] = []

    async def name_taken(self, name: str) -> bool:
        return any(same_name(a.name) == same_name(name) for a in self.items if not a.archived_at)

    async def add(self, account: Account) -> None:
        self.items.append(account)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.accounts = InMemoryAccounts()
        self.committed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass


def account(account_type: AccountType = AccountType.SAVINGS, balance: str = "0") -> Account:
    return Account(
        user_id=USER,
        name=" Galicia ",
        type=account_type,
        currency=Currency.ARS,
        initial_balance=Decimal(balance),
    )


def test_only_broker_accounts_can_start_negative() -> None:
    assert account(AccountType.BROKER, "-1500.50").initial_balance == Decimal("-1500.50")
    for account_type in set(AccountType) - {AccountType.BROKER}:
        with pytest.raises(InvalidAccountError):
            account(account_type, "-0.01")


def test_initial_balance_has_at_most_two_decimals_and_name_is_trimmed() -> None:
    assert account(balance="10.5").name == "Galicia"
    with pytest.raises(InvalidAccountError):
        account(balance="10.001")


async def test_create_account_rejects_a_repeated_name_ignoring_case() -> None:
    uow = FakeUnitOfWork()
    create = CreateAccount(uow=uow)
    await create(
        user_id=USER,
        name="Galicia",
        account_type=AccountType.SAVINGS,
        currency=Currency.ARS,
        initial_balance=Decimal("1000.00"),
    )
    uow.committed = False

    with pytest.raises(AccountNameTakenError):
        await create(
            user_id=USER,
            name="  GALICIA ",
            account_type=AccountType.CASH,
            currency=Currency.USD,
            initial_balance=Decimal("0"),
        )
    assert not uow.committed
    assert len(uow.accounts.items) == 1
