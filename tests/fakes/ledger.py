"""Dobles en memoria para los casos de uso del ledger."""

from types import TracebackType
from typing import Self

from app.modules.ledger.domain.category import Category


class InMemoryCategories:
    def __init__(self) -> None:
        self.items: list[Category] = []

    async def has_any(self) -> bool:
        return bool(self.items)

    async def add_defaults(self, categories: list[Category]) -> None:
        self.items.extend(categories)

    async def list_categories(self) -> list[Category]:
        return list(self.items)


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
