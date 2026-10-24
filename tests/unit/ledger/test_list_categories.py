from collections import Counter
from uuid import uuid4

from app.modules.ledger.application.list_categories import ListCategories
from app.modules.ledger.domain.category import Category, CategoryKind
from fakes.ledger import FakeLedgerUnitOfWork


async def test_first_use_creates_the_default_categories_once() -> None:
    uow = FakeLedgerUnitOfWork()
    user_id = uuid4()
    list_categories = ListCategories(uow=uow)

    first = await list_categories(user_id)
    second = await list_categories(user_id)

    assert Counter(c.kind for c in first) == {CategoryKind.EXPENSE: 9, CategoryKind.INCOME: 4}
    assert {c.name for c in first if c.kind is CategoryKind.INCOME} == {
        "Sueldo",
        "Freelance",
        "Rentas",
        "Otros",
    }
    assert [c.id for c in second] == [c.id for c in first]
    assert uow.commits == 1


async def test_a_user_with_categories_does_not_get_the_defaults() -> None:
    uow = FakeLedgerUnitOfWork()
    user_id = uuid4()
    uow.categories.items.append(Category(user_id, "Mascotas", CategoryKind.EXPENSE))

    categories = await ListCategories(uow=uow)(user_id)

    assert [c.name for c in categories] == ["Mascotas"]
