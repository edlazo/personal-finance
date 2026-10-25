from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.ledger.application.create_transfer import CreateTransfer
from app.modules.ledger.domain.account import Account, AccountType
from app.modules.ledger.domain.category import CategoryKind
from app.modules.ledger.domain.transaction import InvalidTransactionError, Transaction
from app.shared.domain.errors import NotFoundError
from app.shared.domain.money import Currency
from fakes.ledger import FakeLedgerUnitOfWork

USER = uuid4()


def add(uow: FakeLedgerUnitOfWork, name: str, currency: Currency = Currency.ARS) -> Account:
    account = Account(USER, name, AccountType.SAVINGS, currency, Decimal("0"))
    uow.accounts.items[account.id] = account
    return account


async def send(uow: FakeLedgerUnitOfWork, source: Account, target: Account) -> None:
    await CreateTransfer(uow=uow)(
        USER,
        source_id=source.id,
        target_id=target.id,
        amount=Decimal("300.00"),
        on=date(2026, 10, 24),
    )


async def test_a_transfer_is_an_expense_and_an_income_linked_by_group() -> None:
    uow = FakeLedgerUnitOfWork()
    galicia, efectivo = add(uow, "Galicia"), add(uow, "Efectivo")

    await send(uow, galicia, efectivo)

    out, inc = uow.transactions.items
    assert (out.account_id, out.kind, inc.account_id, inc.kind) == (
        galicia.id,
        CategoryKind.EXPENSE,
        efectivo.id,
        CategoryKind.INCOME,
    )
    assert out.transfer_group_id == inc.transfer_group_id is not None
    assert (out.category_id, uow.commits) == (None, 1)


async def test_transfer_rules() -> None:
    uow = FakeLedgerUnitOfWork()
    galicia, dolares, archivada = add(uow, "Galicia"), add(uow, "USD", Currency.USD), add(uow, "X")
    archivada.archive()

    with pytest.raises(InvalidTransactionError, match="distintas"):
        await send(uow, galicia, galicia)
    with pytest.raises(InvalidTransactionError, match="misma moneda"):
        await send(uow, galicia, dolares)
    with pytest.raises(InvalidTransactionError, match="archivada"):
        await send(uow, galicia, archivada)
    ajena = Account(uuid4(), "Ajena", AccountType.CASH, Currency.ARS, Decimal("0"))
    with pytest.raises(NotFoundError):
        await send(uow, galicia, ajena)
    assert uow.transactions.items == []


def test_a_movement_has_a_category_or_belongs_to_a_transfer() -> None:
    with pytest.raises(InvalidTransactionError, match="categoría o es una transferencia"):
        Transaction(USER, uuid4(), CategoryKind.EXPENSE, Decimal("1.00"), date(2026, 10, 24), None)
