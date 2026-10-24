"""Tabla, repositorio y Unit of Work del ledger."""

from datetime import datetime
from typing import Self
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.ledger.domain.category import Category, CategoryKind, CategoryNameTakenError
from app.shared.infrastructure.database import Base
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.infrastructure.user_scoped import UserOwnedMixin, UserScopedRepository


class CategoryModel(UserOwnedMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        # Nombre único por usuario, tipo y padre entre las activas ("Otros" existe como gasto
        # y como ingreso). NULLS NOT DISTINCT: también entre las principales (sin padre).
        Index(
            "uq_categories_user_id_kind_parent_id_name",
            "user_id",
            "kind",
            "parent_id",
            text("lower(name)"),
            unique=True,
            postgresql_nulls_not_distinct=True,
            postgresql_where=text("archived_at IS NULL"),
        ),
    )

    name: Mapped[str] = mapped_column(String(50))
    kind: Mapped[CategoryKind] = mapped_column(
        Enum(CategoryKind, name="category_kind", native_enum=False, length=10)
    )
    parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("categories.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


def _to_domain(m: CategoryModel) -> Category:
    return Category(
        id=m.id,
        user_id=m.user_id,
        name=m.name,
        kind=m.kind,
        parent_id=m.parent_id,
        created_at=m.created_at,
        archived_at=m.archived_at,
    )


def _to_model(c: Category) -> CategoryModel:
    return CategoryModel(
        id=c.id,
        user_id=c.user_id,
        name=c.name,
        kind=c.kind,
        parent_id=c.parent_id,
        created_at=c.created_at,
        archived_at=c.archived_at,
    )


class SqlAlchemyCategoryRepository(UserScopedRepository[CategoryModel]):
    model = CategoryModel

    async def has_any(self) -> bool:
        return await self.session.scalar(select(self.scoped().exists())) or False

    async def add_defaults(self, categories: list[Category]) -> None:
        self.session.add_all(_to_model(c) for c in categories)
        try:
            await self.session.flush()
        except IntegrityError:
            # Dos primeros usos simultáneos: el índice único deja pasar uno solo.
            await self.session.rollback()

    async def list_categories(self, *, include_archived: bool = False) -> list[Category]:
        query = self.scoped().order_by(CategoryModel.kind, CategoryModel.name)
        if not include_archived:
            query = query.where(CategoryModel.archived_at.is_(None))
        return [_to_domain(m) for m in await self.session.scalars(query)]

    async def get_category(self, category_id: UUID) -> Category:
        return _to_domain(await self.get(category_id))

    async def name_taken(self, category: Category) -> bool:
        query = self.scoped().where(
            CategoryModel.id != category.id,
            CategoryModel.kind == category.kind,
            CategoryModel.parent_id.is_not_distinct_from(category.parent_id),
            func.lower(CategoryModel.name) == category.name.lower(),
            CategoryModel.archived_at.is_(None),
        )
        return await self.session.scalar(select(query.exists())) or False

    async def has_children(self, category_id: UUID) -> bool:
        children = self.scoped().where(
            CategoryModel.parent_id == category_id, CategoryModel.archived_at.is_(None)
        )
        return await self.session.scalar(select(children.exists())) or False

    async def add(self, category: Category) -> None:
        self.session.add(_to_model(category))
        try:
            await self.session.flush()
        except IntegrityError as exc:
            # Dos altas simultáneas con el mismo nombre: las frena el índice único.
            raise CategoryNameTakenError from exc

    async def save(self, category: Category) -> None:
        try:
            await self.session.execute(
                update(CategoryModel)
                .where(CategoryModel.id == category.id, CategoryModel.user_id == self.user_id)
                .values(
                    name=category.name,
                    parent_id=category.parent_id,
                    archived_at=category.archived_at,
                )
            )
        except IntegrityError as exc:
            # Dos renombres simultáneos al mismo nombre: los frena el índice único.
            raise CategoryNameTakenError from exc

    async def archive_children(self, parent_id: UUID) -> None:
        await self.session.execute(
            update(CategoryModel)
            .where(
                CategoryModel.user_id == self.user_id,
                CategoryModel.parent_id == parent_id,
                CategoryModel.archived_at.is_(None),
            )
            .values(archived_at=func.now())
        )


class SqlAlchemyLedgerUnitOfWork(SqlAlchemyUnitOfWork):
    categories: SqlAlchemyCategoryRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], user_id: UUID) -> None:
        super().__init__(session_factory)
        self._user_id = user_id

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self.categories = SqlAlchemyCategoryRepository(self.session, self._user_id)
        return self
