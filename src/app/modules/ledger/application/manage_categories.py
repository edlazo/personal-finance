"""Casos de uso: crear, editar y archivar categorías.

Todos aseguran antes las categorías por defecto: si no, crear la primera categoría propia
haría que el usuario nunca recibiera las de por defecto.
"""

from dataclasses import dataclass
from uuid import UUID

from app.modules.ledger.application.list_categories import (
    LedgerUnitOfWork,
    ensure_default_categories,
)
from app.modules.ledger.domain.category import (
    Category,
    CategoryKind,
    CategoryNameTakenError,
    InvalidCategoryError,
    check_parent,
)


@dataclass(frozen=True)
class CreateCategory:
    uow: LedgerUnitOfWork

    async def __call__(
        self, user_id: UUID, *, name: str, kind: CategoryKind, parent_id: UUID | None = None
    ) -> Category:
        async with self.uow:
            await ensure_default_categories(self.uow, user_id)
            category = Category(user_id=user_id, name=name, kind=kind, parent_id=parent_id)
            if parent_id is not None:
                check_parent(kind, await self.uow.categories.get_category(parent_id))
            if await self.uow.categories.name_taken(category):
                raise CategoryNameTakenError
            await self.uow.categories.add(category)
            await self.uow.commit()
        return category


@dataclass(frozen=True)
class UpdateCategory:
    uow: LedgerUnitOfWork

    async def __call__(
        self,
        user_id: UUID,
        category_id: UUID,
        *,
        name: str | None = None,
        change_parent: bool = False,
        parent_id: UUID | None = None,
    ) -> Category:
        """`change_parent=True` con `parent_id=None` la convierte en categoría principal."""
        async with self.uow:
            await ensure_default_categories(self.uow, user_id)
            category = await self.uow.categories.get_category(category_id)
            category.ensure_editable()
            if name is not None:
                category.name = name.strip()
            if change_parent:
                if parent_id is not None:
                    await self._check_new_parent(category, parent_id)
                category.parent_id = parent_id
            if await self.uow.categories.name_taken(category):
                raise CategoryNameTakenError
            await self.uow.categories.save(category)
            await self.uow.commit()
        return category

    async def _check_new_parent(self, category: Category, parent_id: UUID) -> None:
        if parent_id == category.id:
            raise InvalidCategoryError("Una categoría no puede ser su propia subcategoría")
        check_parent(category.kind, await self.uow.categories.get_category(parent_id))
        if await self.uow.categories.has_children(category.id):
            raise InvalidCategoryError("Una categoría con subcategorías no puede ser subcategoría")


@dataclass(frozen=True)
class ArchiveCategory:
    uow: LedgerUnitOfWork

    async def __call__(self, user_id: UUID, category_id: UUID) -> None:
        """Decisión del PO: archiva también sus subcategorías activas. Idempotente."""
        async with self.uow:
            await ensure_default_categories(self.uow, user_id)
            category = await self.uow.categories.get_category(category_id)
            category.archive()
            await self.uow.categories.save(category)
            await self.uow.categories.archive_children(category.id)
            await self.uow.commit()
