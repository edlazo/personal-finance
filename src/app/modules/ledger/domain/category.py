"""Categorías de ingresos y gastos."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4


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
        "Otros",
    ),
    CategoryKind.INCOME: ("Sueldo", "Freelance", "Rentas", "Otros"),
}


@dataclass
class Category:
    user_id: UUID
    name: str
    kind: CategoryKind
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def default_categories(user_id: UUID) -> list[Category]:
    return [
        Category(user_id=user_id, name=name, kind=kind)
        for kind, names in DEFAULT_CATEGORIES.items()
        for name in names
    ]


class CategoryRepository(Protocol):
    """Repositorio de las categorías de un usuario (ya filtrado por su dueño)."""

    async def has_any(self) -> bool: ...

    async def add_defaults(self, categories: list[Category]) -> None:
        """Si otro pedido simultáneo ya las creó, no hace nada."""
        ...

    async def list_categories(self) -> list[Category]: ...
