"""Tabla, repositorio y Unit of Work del ledger."""

from datetime import datetime
from typing import Self
from uuid import UUID

from sqlalchemy import DateTime, Enum, Index, String, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.ledger.domain.category import Category, CategoryKind
from app.shared.infrastructure.database import Base
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.infrastructure.user_scoped import UserOwnedMixin, UserScopedRepository


class CategoryModel(UserOwnedMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        # Nombre único por usuario y tipo ("Otros" existe como gasto y como ingreso).
        Index(
            "uq_categories_user_id_kind_name", "user_id", "kind", text("lower(name)"), unique=True
        ),
    )

    name: Mapped[str] = mapped_column(String(50))
    kind: Mapped[CategoryKind] = mapped_column(
        Enum(CategoryKind, name="category_kind", native_enum=False, length=10)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SqlAlchemyCategoryRepository(UserScopedRepository[CategoryModel]):
    model = CategoryModel

    async def has_any(self) -> bool:
        return await self.session.scalar(select(self.scoped().exists())) or False

    async def add_defaults(self, categories: list[Category]) -> None:
        self.session.add_all(
            CategoryModel(
                id=c.id, user_id=c.user_id, name=c.name, kind=c.kind, created_at=c.created_at
            )
            for c in categories
        )
        try:
            await self.session.flush()
        except IntegrityError:
            # Dos primeros usos simultáneos: el índice único deja pasar uno solo.
            await self.session.rollback()

    async def list_categories(self) -> list[Category]:
        query = self.scoped().order_by(CategoryModel.kind, CategoryModel.name)
        return [
            Category(id=m.id, user_id=m.user_id, name=m.name, kind=m.kind, created_at=m.created_at)
            for m in await self.session.scalars(query)
        ]


class SqlAlchemyLedgerUnitOfWork(SqlAlchemyUnitOfWork):
    categories: SqlAlchemyCategoryRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], user_id: UUID) -> None:
        super().__init__(session_factory)
        self._user_id = user_id

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self.categories = SqlAlchemyCategoryRepository(self.session, self._user_id)
        return self
