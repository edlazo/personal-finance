from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.ledger.application.create_transfer import CreateTransfer
from app.modules.ledger.domain.account import Account, AccountType
from app.modules.ledger.domain.category import Category, CategoryKind
from app.modules.ledger.domain.transaction import InvalidTransactionError, Transaction
from app.shared.domain.errors import NotFoundError
from app.shared.domain.money import Currency
from fakes.ledger import FakeLedgerUnitOfWork

USER = uuid4()


def add(uow: FakeLedgerUnitOfWork, name: str, currency: Currency = Currency.ARS) -> Account:
    account = Account(USER, name, AccountType.SAVINGS, currency, Decimal("1000000"))
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
    with pytest.raises(InvalidTransactionError, match="monto que entra"):
        await send(uow, galicia, dolares)
    with pytest.raises(InvalidTransactionError, match="archivada"):
        await send(uow, galicia, archivada)
    ajena = Account(uuid4(), "Ajena", AccountType.CASH, Currency.ARS, Decimal("0"))
    with pytest.raises(NotFoundError):
        await send(uow, galicia, ajena)
    assert uow.transactions.items == []


def test_a_movement_has_a_category_or_belongs_to_a_transfer() -> None:
    with pytest.raises(InvalidTransactionError, match="categoría o es parte de"):
        Transaction(USER, uuid4(), CategoryKind.EXPENSE, Decimal("1.00"), date(2026, 10, 24), None)


async def test_buying_and_selling_dollars_keeps_each_amount_and_the_rate() -> None:
    uow = FakeLedgerUnitOfWork()
    pesos, dolares = add(uow, "Galicia"), add(uow, "Dólares", Currency.USD)
    create = CreateTransfer(uow=uow)
    day = date(2026, 10, 24)

    bought = await create(
        USER,
        source_id=pesos.id,
        target_id=dolares.id,
        amount=Decimal("125000"),
        on=day,
        received=Decimal("100"),
    )
    sold = await create(
        USER,
        source_id=dolares.id,
        target_id=pesos.id,
        amount=Decimal("50"),
        on=day,
        received=Decimal("60000"),
    )

    assert (bought.outgoing.amount, bought.incoming.amount) == (Decimal("125000"), Decimal("100"))
    assert (bought.exchange_rate, sold.exchange_rate) == (
        Decimal("1250.0000"),
        Decimal("1200.0000"),
    )
    with pytest.raises(InvalidTransactionError, match="mismo monto"):
        await create(
            USER,
            source_id=pesos.id,
            target_id=add(uow, "Caja").id,
            amount=Decimal("10"),
            on=day,
            received=Decimal("9"),
        )


async def test_the_fee_is_a_separate_expense_in_comisiones_created_if_missing() -> None:
    uow = FakeLedgerUnitOfWork()
    # Usuario de antes de esta versión: ya tiene categorías, pero no "Comisiones".
    ocio = Category(USER, "Ocio", CategoryKind.EXPENSE)
    uow.categories.items[ocio.id] = ocio
    pesos, dolares = add(uow, "Galicia"), add(uow, "Dólares", Currency.USD)

    async def buy() -> Transaction | None:
        result = await CreateTransfer(uow=uow)(
            USER,
            source_id=pesos.id,
            target_id=dolares.id,
            amount=Decimal("1250"),
            on=date(2026, 10, 24),
            received=Decimal("1"),
            fee=Decimal("12.50"),
        )
        return result.fee

    first, second = await buy(), await buy()

    fees = [c for c in uow.categories.items.values() if c.name == "Comisiones"]
    assert len(fees) == 1
    assert first is not None
    assert second is not None
    assert (first.account_id, first.amount, first.category_id) == (
        pesos.id,
        Decimal("12.50"),
        fees[0].id,
    )
    assert (first.transfer_group_id, second.category_id) == (None, fees[0].id)
