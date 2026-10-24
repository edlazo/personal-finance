"""Dobles en memoria para los casos de uso del ledger."""

from types import TracebackType
from typing import Self
from uuid import UUID

from app.modules.ledger.domain.category import Category
from app.shared.domain.errors import NotFoundError


class InMemoryCategories:
    def __init__(self) -> None:
        self.items: dict[UUID, Category] = {}

    async def has_any(self) -> bool:
        return bool(self.items)

    async def add_defaults(self, categories: list[Category]) -> None:
        self.items.update((c.id, c) for c in categories)

    async def list_categories(self, *, include_archived: bool = False) -> list[Category]:
        return [c for c in self.items.values() if include_archived or c.archived_at is None]

    async def get_category(self, category_id: UUID) -> Category:
        if category_id not in self.items:
            raise NotFoundError("El recurso no existe")
        return self.items[category_id]

    async def name_taken(self, category: Category) -> bool:
        return any(
            c.id != category.id
            and c.archived_at is None
            and (c.kind, c.parent_id, c.name.lower())
            == (category.kind, category.parent_id, category.name.lower())
            for c in self.items.values()
        )

    async def has_children(self, category_id: UUID) -> bool:
        return any(c.parent_id == category_id and not c.archived_at for c in self.items.values())

    async def add(self, category: Category) -> None:
        self.items[category.id] = category

    async def save(self, category: Category) -> None:
        self.items[category.id] = category

    async def archive_children(self, parent_id: UUID) -> None:
        for child in self.items.values():
            if child.parent_id == parent_id:
                child.archive()


class FakeLedgerUnitOfWork:
    def __init__(self) -> None:
        self.categories = InMemoryCategories()
        self.commits = 0

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
        self.commits += 1

    async def rollback(self) -> None:
        pass
