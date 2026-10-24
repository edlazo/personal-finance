"""Aislamiento multiusuario: todo recurso propio se lee filtrando por su dueño."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import ForeignKey, Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.domain.errors import NotFoundError


class UserOwnedMixin:
    """Columnas de un recurso que pertenece a un usuario."""

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)


class UserScopedRepository[M: UserOwnedMixin]:
    """Base de los repositorios de recursos propios: nunca devuelve datos de otro usuario."""

    model: type[M]

    def __init__(self, session: AsyncSession, user_id: UUID) -> None:
        self.session = session
        self.user_id = user_id

    def scoped(self) -> Select[M]:
        """Punto de partida de toda consulta: ya filtrado por el usuario actual."""
        return select(self.model).where(self.model.user_id == self.user_id)

    async def get(self, resource_id: UUID) -> M:
        found = await self.session.scalar(self.scoped().where(self.model.id == resource_id))
        if found is None:
            # 404 tanto si no existe como si es de otro usuario: no se revela cuál.
            raise NotFoundError("El recurso no existe")
        return found

    async def list(self) -> Sequence[M]:
        return (await self.session.scalars(self.scoped())).all()
