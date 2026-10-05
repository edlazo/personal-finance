"""Engine, sesiones y base declarativa de SQLAlchemy (async)."""

import asyncio

from sqlalchemy import MetaData, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# Nombres de constraints deterministas: Alembic puede generar y revertir migraciones sin adivinar.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def create_engine(url: str) -> AsyncEngine:
    return create_async_engine(url, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


PING_TIMEOUT_SECONDS = 3.0


async def ping(engine: AsyncEngine) -> bool:
    """True si la base responde a `SELECT 1` dentro de PING_TIMEOUT_SECONDS."""
    try:
        async with asyncio.timeout(PING_TIMEOUT_SECONDS), engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError, OSError, TimeoutError:
        return False
    return True
