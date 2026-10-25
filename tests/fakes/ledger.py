"""Dobles en memoria para los casos de uso del ledger."""

from types import TracebackType
from typing import Self
from uuid import UUID

from app.modules.ledger.domain.category import Category
from app.modules.ledger.domain.transaction import Transaction, TransactionFilter
from app.shared.domain.errors import NotFoundError
from fakes.accounts import InMemoryAccounts


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


class InMemoryTransactions:
    def __init__(self) -> None:
        self.items: list[Transaction] = []

    async def add(self, transaction: Transaction) -> None:
        self.items.append(transaction)

    async def search(
        self, filters: TransactionFilter, *, limit: int, offset: int
    ) -> tuple[list[Transaction], int]:
        # shortcut: solo filtra por categorías; el resto de los filtros se prueba contra Postgres.
        found = [
            t
            for t in self.items
            if filters.category_ids is None or t.category_id in filters.category_ids
        ]
        found.sort(key=lambda t: (t.date, t.created_at), reverse=True)
        return found[offset : offset + limit], len(found)

    async def get_transaction(self, transaction_id: UUID) -> Transaction:
        for transaction in self.items:
            if transaction.id == transaction_id:
                return transaction
        raise NotFoundError("El recurso no existe")

    async def transfer_legs(self, group_id: UUID) -> list[Transaction]:
        return [t for t in self.items if t.transfer_group_id == group_id]

    async def save(self, transaction: Transaction) -> None:
        self.items = [transaction if t.id == transaction.id else t for t in self.items]

    async def delete(self, transaction_id: UUID) -> None:
        self.items = [t for t in self.items if t.id != transaction_id]


class FakeLedgerUnitOfWork:
    def __init__(self) -> None:
        self.accounts = InMemoryAccounts()
        self.categories = InMemoryCategories()
        self.transactions = InMemoryTransactions()
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
