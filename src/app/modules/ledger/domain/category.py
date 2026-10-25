"""Categorías de ingresos y gastos."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from app.shared.domain.errors import ConflictError, DomainError


class CategoryKind(StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


DEFAULT_CATEGORIES: dict[CategoryKind, tuple[str, ...]] = {
    CategoryKind.EXPENSE: (
        "Supermercado",
        "Servicios",
        "Alquiler",
        "Transporte",
        "Salud",
        "Ocio",
        "Educación",
        "Impuestos",
        "Comisiones",
        "Otros",
    ),
    CategoryKind.INCOME: ("Sueldo", "Freelance", "Rentas", "Otros"),
}


class InvalidCategoryError(DomainError):
    pass


class CategoryNameTakenError(ConflictError):
    def __init__(self) -> None:
        super().__init__("Ya tenés una categoría activa con ese nombre en ese lugar")


class CategoryArchivedError(ConflictError):
    def __init__(self) -> None:
        super().__init__("La categoría está archivada y no se puede editar")


@dataclass
class Category:
    user_id: UUID
    name: str
    kind: CategoryKind
    parent_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    archived_at: datetime | None = None

    def __post_init__(self) -> None:
        self.name = self.name.strip()

    def ensure_editable(self) -> None:
        # Decisión del PO: las archivadas son de solo lectura, como las cuentas.
        if self.archived_at is not None:
            raise CategoryArchivedError

    def archive(self) -> None:
        if self.archived_at is None:
            self.archived_at = datetime.now(UTC)


def check_parent(kind: CategoryKind, parent: Category) -> None:
    """Reglas de una subcategoría: un solo nivel, mismo tipo, padre activo."""
    if parent.archived_at is not None:
        raise InvalidCategoryError("La categoría padre está archivada")
    if parent.parent_id is not None:
        raise InvalidCategoryError("Solo se admite un nivel de subcategorías")
    if parent.kind is not kind:
        raise InvalidCategoryError("La subcategoría debe ser del mismo tipo que su padre")


def default_categories(user_id: UUID) -> list[Category]:
    return [
        Category(user_id=user_id, name=name, kind=kind)
        for kind, names in DEFAULT_CATEGORIES.items()
        for name in names
    ]


class CategoryRepository(Protocol):
    """Repositorio de las categorías de un usuario (ya filtrado por su dueño)."""

    async def has_any(self) -> bool:
        """Incluye archivadas: así las categorías por defecto no vuelven a crearse."""
        ...

    async def add_defaults(self, categories: list[Category]) -> None:
        """Si otro pedido simultáneo ya las creó, no hace nada."""
        ...

    async def list_categories(self, *, include_archived: bool = False) -> list[Category]: ...

    async def get_category(self, category_id: UUID) -> Category:
        """NotFoundError si no existe o es de otro usuario."""
        ...

    async def name_taken(self, category: Category) -> bool:
        """Otra categoría activa del mismo tipo y padre usa ese nombre."""
        ...

    async def has_children(self, category_id: UUID) -> bool: ...

    async def add(self, category: Category) -> None: ...

    async def save(self, category: Category) -> None: ...

    async def archive_children(self, parent_id: UUID) -> None: ...
