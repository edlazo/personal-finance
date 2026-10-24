"""Caso de uso: listar las categorías del usuario."""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.modules.ledger.domain.category import Category, CategoryRepository, default_categories
from app.shared.application.unit_of_work import UnitOfWork


class LedgerUnitOfWork(UnitOfWork, Protocol):
    @property
    def categories(self) -> CategoryRepository: ...


async def ensure_default_categories(uow: LedgerUnitOfWork, user_id: UUID) -> None:
    """Decisión del PO: las categorías por defecto se crean en el primer uso, no al registrarse.

    Se llama dentro de una transacción abierta, antes de leer o usar categorías.
    """
    if not await uow.categories.has_any():
        await uow.categories.add_defaults(default_categories(user_id))
        await uow.commit()


@dataclass(frozen=True)
class ListCategories:
    uow: LedgerUnitOfWork

    async def __call__(self, user_id: UUID, *, include_archived: bool = False) -> list[Category]:
        async with self.uow:
            await ensure_default_categories(self.uow, user_id)
            return await self.uow.categories.list_categories(include_archived=include_archived)
