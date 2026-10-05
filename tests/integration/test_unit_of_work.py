from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.shared.application.unit_of_work import UnitOfWork
from app.shared.infrastructure.database import create_session_factory
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork

pytestmark = pytest.mark.integration


@pytest.fixture
async def session_factory(engine: AsyncEngine) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    async with engine.begin() as connection:
        await connection.execute(text("CREATE TABLE uow_probe (id integer PRIMARY KEY)"))
    yield create_session_factory(engine)
    async with engine.begin() as connection:
        await connection.execute(text("DROP TABLE uow_probe"))


async def insert_probe(uow: SqlAlchemyUnitOfWork) -> None:
    await uow.session.execute(text("INSERT INTO uow_probe (id) VALUES (1)"))


async def count_probes(session_factory: async_sessionmaker[AsyncSession]) -> int:
    async with session_factory() as session:
        return int((await session.execute(text("SELECT count(*) FROM uow_probe"))).scalar_one())


# El chequeo real es de mypy: SqlAlchemyUnitOfWork tiene que cumplir el Protocol.
def test_implements_port(session_factory: async_sessionmaker[AsyncSession]) -> None:
    uow: UnitOfWork = SqlAlchemyUnitOfWork(session_factory)
    assert isinstance(uow, SqlAlchemyUnitOfWork)


async def test_commit_persists(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await insert_probe(uow)
        await uow.commit()

    assert await count_probes(session_factory) == 1


async def test_without_commit_discards(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await insert_probe(uow)

    assert await count_probes(session_factory) == 0


async def test_exception_discards(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async def failing_use_case() -> None:
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            await insert_probe(uow)
            raise RuntimeError

    with pytest.raises(RuntimeError):
        await failing_use_case()

    assert await count_probes(session_factory) == 0
