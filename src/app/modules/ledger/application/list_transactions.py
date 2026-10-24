"""Caso de uso: buscar movimientos con filtros y paginación."""

from dataclasses import dataclass, replace
from uuid import UUID

from app.modules.ledger.application.create_transaction import TransactionsUnitOfWork
from app.modules.ledger.domain.transaction import Transaction, TransactionFilter


@dataclass(frozen=True)
class TransactionPage:
    items: list[Transaction]
    total: int


@dataclass(frozen=True)
class ListTransactions:
    uow: TransactionsUnitOfWork

    async def __call__(
        self,
        filters: TransactionFilter,
        *,
        category_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> TransactionPage:
        async with self.uow:
            if category_id is not None:
                # Filtrar por una categoría padre incluye sus subcategorías.
                categories = await self.uow.categories.list_categories(include_archived=True)
                children = {c.id for c in categories if c.parent_id == category_id}
                filters = replace(filters, category_ids=frozenset({category_id} | children))
            items, total = await self.uow.transactions.search(filters, limit=limit, offset=offset)
        return TransactionPage(items, total)
