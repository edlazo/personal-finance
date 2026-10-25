from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.identity.domain.user import EmailAlreadyRegisteredError, User
from app.modules.identity.infrastructure.persistence import SqlAlchemyIdentityUnitOfWork
from app.shared.infrastructure.database import create_session_factory

pytestmark = pytest.mark.integration


def new_email() -> str:
    return f"usuario-{uuid4().hex[:8]}@example.com"


async def test_repository_saves_and_finds_by_email(
    migrated_database_url: str, engine: AsyncEngine
) -> None:
    session_factory = create_session_factory(engine)
    user = User(email=new_email(), name="Ana", password_hash="hash")
    async with SqlAlchemyIdentityUnitOfWork(session_factory) as uow:
        await uow.users.add(user)
        await uow.commit()

    async with SqlAlchemyIdentityUnitOfWork(session_factory) as uow:
        assert await uow.users.get_by_email(user.email) == user
        assert await uow.users.get_by_email(new_email()) is None


async def test_unique_index_blocks_simultaneous_duplicates(
    migrated_database_url: str, engine: AsyncEngine
) -> None:
    # Simula dos registros que pasaron a la vez la verificación previa del caso de uso.
    session_factory = create_session_factory(engine)
    email = new_email()
    async with SqlAlchemyIdentityUnitOfWork(session_factory) as uow:
        await uow.users.add(User(email=email, name="Ana", password_hash="hash-1"))
        await uow.commit()

    with pytest.raises(EmailAlreadyRegisteredError):
        async with SqlAlchemyIdentityUnitOfWork(session_factory) as uow:
            await uow.users.add(User(email=email, name="Otra", password_hash="hash-2"))
