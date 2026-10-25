from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.ledger.application.create_transfer import CreateTransfer
from app.modules.ledger.application.manage_transactions import (
    DeleteTransaction,
    UpdateTransaction,
)
from app.modules.ledger.domain.account import Account, AccountArchivedError, AccountType
from app.modules.ledger.domain.category import Category, CategoryKind
from app.modules.ledger.domain.transaction import InvalidTransactionError, Transaction
from app.shared.domain.money import Currency
from fakes.ledger import FakeLedgerUnitOfWork

USER = uuid4()
EXPENSE, INCOME = CategoryKind.EXPENSE, CategoryKind.INCOME
DAY = date(2026, 10, 24)


@pytest.fixture
def uow() -> FakeLedgerUnitOfWork:
    return FakeLedgerUnitOfWork()


def account(uow: FakeLedgerUnitOfWork, name: str = "Galicia") -> Account:
    created = Account(USER, name, AccountType.SAVINGS, Currency.ARS, Decimal("0"))
    uow.accounts.items[created.id] = created
    return created


def category(uow: FakeLedgerUnitOfWork, kind: CategoryKind = EXPENSE) -> Category:
    created = Category(USER, f"Categoría {kind}", kind)
    uow.categories.items[created.id] = created
    return created


def expense(uow: FakeLedgerUnitOfWork, galicia: Account, ocio: Category) -> Transaction:
    created = Transaction(USER, galicia.id, EXPENSE, Decimal("10.00"), DAY, ocio.id, "Cine")
    uow.transactions.items.append(created)
    return created


async def transfer(uow: FakeLedgerUnitOfWork) -> tuple[Transaction, Transaction]:
    result = await CreateTransfer(uow=uow)(
        USER,
        source_id=account(uow).id,
        target_id=account(uow, "Caja").id,
        amount=Decimal("300.00"),
        on=DAY,
    )
    return result.outgoing, result.incoming


async def test_edits_a_movement_and_rechecks_its_category(uow: FakeLedgerUnitOfWork) -> None:
    galicia, ocio, sueldo = account(uow), category(uow), category(uow, INCOME)
    movement = expense(uow, galicia, ocio)
    update = UpdateTransaction(uow=uow)

    edited = await update(movement.id, amount=Decimal("12.50"), description="  ")
    with pytest.raises(InvalidTransactionError, match="no coincide"):
        await update(movement.id, category_id=sueldo.id)
    switched = await update(movement.id, kind=INCOME, category_id=sueldo.id)

    assert (edited.amount, edited.description, edited.created_at) == (
        Decimal("12.50"),
        None,
        movement.created_at,
    )
    assert (switched.kind, uow.transactions.items) == (INCOME, [switched])


async def test_editing_or_deleting_one_leg_changes_both(uow: FakeLedgerUnitOfWork) -> None:
    outgoing, incoming = await transfer(uow)
    update = UpdateTransaction(uow=uow)

    await update(incoming.id, amount=Decimal("250.00"), on=date(2026, 10, 1))
    with pytest.raises(InvalidTransactionError, match="solo se editan"):
        await update(outgoing.id, account_id=uuid4())

    assert {(t.amount, t.date) for t in uow.transactions.items} == {
        (Decimal("250.00"), date(2026, 10, 1))
    }
    await DeleteTransaction(uow=uow)(outgoing.id)
    assert uow.transactions.items == []


async def test_movements_of_an_archived_account_are_read_only(uow: FakeLedgerUnitOfWork) -> None:
    galicia = account(uow)
    movement = expense(uow, galicia, category(uow))
    galicia.archive()

    with pytest.raises(AccountArchivedError):
        await UpdateTransaction(uow=uow)(movement.id, amount=Decimal("1.00"))
    with pytest.raises(AccountArchivedError):
        await DeleteTransaction(uow=uow)(movement.id)
