from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.ledger.application.create_transaction import CreateTransaction
from app.modules.ledger.application.manage_accounts import UpdateAccount
from app.modules.ledger.domain.account import Account, AccountCurrencyLockedError, AccountType
from app.modules.ledger.domain.category import Category, CategoryKind
from app.modules.ledger.domain.transaction import InvalidTransactionError
from app.shared.domain.errors import NotFoundError
from app.shared.domain.money import Currency
from fakes.ledger import FakeLedgerUnitOfWork

USER = uuid4()
EXPENSE, INCOME = CategoryKind.EXPENSE, CategoryKind.INCOME


@pytest.fixture
def uow() -> FakeLedgerUnitOfWork:
    return FakeLedgerUnitOfWork()


def add_account(uow: FakeLedgerUnitOfWork) -> Account:
    account = Account(USER, "Galicia", AccountType.SAVINGS, Currency.ARS, Decimal("0"))
    uow.accounts.items[account.id] = account
    return account


def add_category(uow: FakeLedgerUnitOfWork, kind: CategoryKind = EXPENSE) -> Category:
    category = Category(USER, "Supermercado", kind)
    uow.categories.items[category.id] = category
    return category


async def register(
    uow: FakeLedgerUnitOfWork,
    account: Account,
    category: Category,
    amount: str = "1500.50",
    kind: CategoryKind = EXPENSE,
) -> None:
    await CreateTransaction(uow=uow)(
        USER,
        account_id=account.id,
        kind=kind,
        amount=Decimal(amount),
        on=date(2026, 10, 24),
        category_id=category.id,
        description="  Compra del mes ",
    )


async def test_registers_an_expense(uow: FakeLedgerUnitOfWork) -> None:
    await register(uow, add_account(uow), add_category(uow))

    [saved] = uow.transactions.items
    assert (saved.amount, saved.description) == (Decimal("1500.50"), "Compra del mes")
    assert uow.commits == 1


@pytest.mark.parametrize("amount", ["0", "-10.00", "10.001"])
async def test_amount_must_be_positive_with_two_decimals(
    uow: FakeLedgerUnitOfWork, amount: str
) -> None:
    with pytest.raises(InvalidTransactionError):
        await register(uow, add_account(uow), add_category(uow), amount=amount)


async def test_category_must_match_the_kind_and_be_active(uow: FakeLedgerUnitOfWork) -> None:
    account = add_account(uow)

    with pytest.raises(InvalidTransactionError, match="no coincide"):
        await register(uow, account, add_category(uow, INCOME))
    archived = add_category(uow)
    archived.archive()
    with pytest.raises(InvalidTransactionError, match="archivada"):
        await register(uow, account, archived)


async def test_no_movements_in_archived_or_unknown_accounts(uow: FakeLedgerUnitOfWork) -> None:
    account, category = add_account(uow), add_category(uow)
    account.archive()

    with pytest.raises(InvalidTransactionError, match="cuenta archivada"):
        await register(uow, account, category)
    unknown = Account(USER, "Otra", AccountType.CASH, Currency.ARS, Decimal("0"))
    with pytest.raises(NotFoundError):
        await register(uow, unknown, category)


async def test_currency_cannot_change_once_the_account_has_movements(
    uow: FakeLedgerUnitOfWork,
) -> None:
    account = add_account(uow)
    update = UpdateAccount(uow=uow)
    await update(account.id, currency=Currency.ARS)  # misma moneda: no es un cambio
    uow.accounts.with_movements.add(account.id)

    with pytest.raises(AccountCurrencyLockedError):
        await update(account.id, currency=Currency.USD)
    assert (await update(account.id, name="Galicia ARS")).name == "Galicia ARS"
