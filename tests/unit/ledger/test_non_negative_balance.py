from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.ledger.application.create_transaction import CreateTransaction
from app.modules.ledger.application.create_transfer import CreateTransfer
from app.modules.ledger.application.manage_transactions import (
    DeleteTransaction,
    UpdateTransaction,
)
from app.modules.ledger.domain.account import Account, AccountType, NegativeBalanceError
from app.modules.ledger.domain.category import Category, CategoryKind
from app.modules.ledger.domain.transaction import Transaction
from app.shared.domain.money import Currency
from fakes.ledger import FakeLedgerUnitOfWork

USER = uuid4()
EXPENSE, INCOME = CategoryKind.EXPENSE, CategoryKind.INCOME


def setup(
    account_type: AccountType = AccountType.SAVINGS,
) -> tuple[FakeLedgerUnitOfWork, Account, Category, Category]:
    uow = FakeLedgerUnitOfWork()
    account = Account(USER, "Galicia", account_type, Currency.ARS, Decimal("0"))
    uow.accounts.items[account.id] = account
    ocio, sueldo = Category(USER, "Ocio", EXPENSE), Category(USER, "Sueldo", INCOME)
    uow.categories.items.update({ocio.id: ocio, sueldo.id: sueldo})
    return uow, account, ocio, sueldo


async def register(
    uow: FakeLedgerUnitOfWork, account: Account, category: Category, amount: str, day: int
) -> Transaction:
    return await CreateTransaction(uow=uow)(
        USER,
        account_id=account.id,
        kind=category.kind,
        amount=Decimal(amount),
        on=date(2026, 10, day),
        category_id=category.id,
    )


async def test_an_expense_cannot_leave_the_account_negative() -> None:
    uow, galicia, ocio, sueldo = setup()
    await register(uow, galicia, sueldo, "100", day=10)

    with pytest.raises(NegativeBalanceError, match=r"Galicia .* 11/10/2026"):
        await register(uow, galicia, ocio, "100.01", day=11)
    await register(uow, galicia, ocio, "100", day=11)


async def test_a_back_dated_expense_cannot_break_a_later_balance() -> None:
    uow, galicia, ocio, sueldo = setup()
    await register(uow, galicia, sueldo, "100", day=10)
    await register(uow, galicia, ocio, "100", day=15)

    # El día 12 el saldo queda en 50, pero el 15 pasaría a -50.
    with pytest.raises(NegativeBalanceError, match="15/10/2026"):
        await register(uow, galicia, ocio, "50", day=12)


async def test_a_broker_account_can_go_negative() -> None:
    uow, broker, ocio, _ = setup(AccountType.BROKER)

    await register(uow, broker, ocio, "500", day=10)


async def test_deleting_income_editing_or_transferring_also_checks_the_balance() -> None:
    uow, galicia, ocio, sueldo = setup()
    income = await register(uow, galicia, sueldo, "100", day=10)
    spent = await register(uow, galicia, ocio, "80", day=11)
    caja = Account(USER, "Caja", AccountType.CASH, Currency.ARS, Decimal("0"))
    uow.accounts.items[caja.id] = caja

    with pytest.raises(NegativeBalanceError):
        await DeleteTransaction(uow=uow)(income.id)
    with pytest.raises(NegativeBalanceError):
        await UpdateTransaction(uow=uow)(spent.id, amount=Decimal("150"))
    with pytest.raises(NegativeBalanceError):
        await CreateTransfer(uow=uow)(
            USER,
            source_id=galicia.id,
            target_id=caja.id,
            amount=Decimal("21"),
            on=date(2026, 10, 12),
        )
