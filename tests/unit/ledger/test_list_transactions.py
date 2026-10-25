from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.modules.ledger.application.list_transactions import ListTransactions
from app.modules.ledger.domain.category import Category, CategoryKind
from app.modules.ledger.domain.transaction import Transaction, TransactionFilter
from fakes.ledger import FakeLedgerUnitOfWork

USER, ACCOUNT = uuid4(), uuid4()


def spend(uow: FakeLedgerUnitOfWork, category: Category, day: int) -> Transaction:
    transaction = Transaction(
        USER, ACCOUNT, CategoryKind.EXPENSE, Decimal("10.00"), date(2026, 10, day), category.id
    )
    uow.transactions.items.append(transaction)
    return transaction


async def test_a_parent_category_includes_its_subcategories_newest_first() -> None:
    uow = FakeLedgerUnitOfWork()
    comida = Category(USER, "Comida", CategoryKind.EXPENSE)
    delivery = Category(USER, "Delivery", CategoryKind.EXPENSE, parent_id=comida.id)
    hogar = Category(USER, "Hogar", CategoryKind.EXPENSE)
    uow.categories.items.update((c.id, c) for c in (comida, delivery, hogar))
    older, newer = spend(uow, comida, 1), spend(uow, delivery, 20)
    spend(uow, hogar, 15)

    page = await ListTransactions(uow=uow)(TransactionFilter(), category_id=comida.id)
    first = await ListTransactions(uow=uow)(TransactionFilter(), limit=1, offset=0)

    assert (page.items, page.total) == ([newer, older], 2)
    assert (first.items, first.total) == ([newer], 3)
