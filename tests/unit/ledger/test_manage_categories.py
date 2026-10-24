from uuid import uuid4

import pytest

from app.modules.ledger.application.list_categories import ListCategories
from app.modules.ledger.application.manage_categories import (
    ArchiveCategory,
    CreateCategory,
    UpdateCategory,
)
from app.modules.ledger.domain.category import (
    Category,
    CategoryArchivedError,
    CategoryKind,
    CategoryNameTakenError,
    InvalidCategoryError,
)
from fakes.ledger import FakeLedgerUnitOfWork

EXPENSE, INCOME = CategoryKind.EXPENSE, CategoryKind.INCOME
USER = uuid4()


@pytest.fixture
def uow() -> FakeLedgerUnitOfWork:
    return FakeLedgerUnitOfWork()


async def create(
    uow: FakeLedgerUnitOfWork,
    name: str,
    kind: CategoryKind = EXPENSE,
    parent: Category | None = None,
) -> Category:
    return await CreateCategory(uow=uow)(
        USER, name=name, kind=kind, parent_id=parent.id if parent else None
    )


async def test_creating_the_first_own_category_keeps_the_defaults(
    uow: FakeLedgerUnitOfWork,
) -> None:
    await create(uow, "Mascotas")

    names = {c.name for c in await ListCategories(uow=uow)(USER)}
    assert {"Mascotas", "Supermercado", "Sueldo"} <= names


async def test_subcategory_rules(uow: FakeLedgerUnitOfWork) -> None:
    comida = await create(uow, "Comida")
    delivery = await create(uow, "Delivery", parent=comida)

    with pytest.raises(InvalidCategoryError, match="un nivel"):
        await create(uow, "Pizza", parent=delivery)
    with pytest.raises(InvalidCategoryError, match="mismo tipo"):
        await create(uow, "Propinas", kind=INCOME, parent=comida)
    # El nombre se repite solo si cambia el padre o el tipo.
    await create(uow, "Delivery")
    with pytest.raises(CategoryNameTakenError):
        await create(uow, " DELIVERY ", parent=comida)


async def test_update_moves_and_renames_with_the_same_rules(uow: FakeLedgerUnitOfWork) -> None:
    comida, hogar = await create(uow, "Comida"), await create(uow, "Hogar")
    delivery = await create(uow, "Delivery", parent=comida)
    update = UpdateCategory(uow=uow)

    moved = await update(USER, delivery.id, name="Envíos", change_parent=True, parent_id=hogar.id)
    top_level = await update(USER, delivery.id, change_parent=True, parent_id=None)

    assert (moved.name, top_level.parent_id) == ("Envíos", None)
    await create(uow, "Limpieza", parent=hogar)
    with pytest.raises(InvalidCategoryError, match="con subcategorías"):
        await update(USER, hogar.id, change_parent=True, parent_id=comida.id)


async def test_archiving_a_parent_archives_its_children_and_makes_it_read_only(
    uow: FakeLedgerUnitOfWork,
) -> None:
    comida = await create(uow, "Comida")
    delivery = await create(uow, "Delivery", parent=comida)

    await ArchiveCategory(uow=uow)(USER, comida.id)
    await ArchiveCategory(uow=uow)(USER, comida.id)

    assert delivery.archived_at is not None
    assert "Comida" not in {c.name for c in await ListCategories(uow=uow)(USER)}
    with pytest.raises(CategoryArchivedError):
        await UpdateCategory(uow=uow)(USER, comida.id, name="Alimentos")
