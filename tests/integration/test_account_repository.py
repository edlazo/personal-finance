from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.modules.accounts.domain.account import Account, AccountNameTakenError, AccountType
from app.modules.accounts.infrastructure.persistence import SqlAlchemyAccountsUnitOfWork
from app.modules.identity.domain.user import User
from app.modules.identity.infrastructure.persistence import SqlAlchemyIdentityUnitOfWork
from app.shared.domain.money import Currency
from app.shared.infrastructure.database import create_session_factory

pytestmark = pytest.mark.integration


@pytest.fixture
def session_factory(
    migrated_database_url: str, engine: AsyncEngine
) -> async_sessionmaker[AsyncSession]:
    return create_session_factory(engine)


@pytest.fixture
def new_user(
    session_factory: async_sessionmaker[AsyncSession],
) -> Callable[[], Awaitable[UUID]]:
    async def create() -> UUID:
        user = User(email=f"cuentas-{uuid4().hex[:8]}@example.com", name="Ana", password_hash="h")
        async with SqlAlchemyIdentityUnitOfWork(session_factory) as uow:
            await uow.users.add(user)
            await uow.commit()
        return user.id

    return create


def galicia(user_id: UUID, name: str = "Galicia", archived: bool = False) -> Account:
    return Account(
        user_id=user_id,
        name=name,
        type=AccountType.SAVINGS,
        currency=Currency.ARS,
        initial_balance=Decimal("1500.50"),
        archived_at=datetime.now(UTC) if archived else None,
    )


async def save(session_factory: async_sessionmaker[AsyncSession], account: Account) -> None:
    async with SqlAlchemyAccountsUnitOfWork(session_factory, account.user_id) as uow:
        await uow.accounts.add(account)
        await uow.commit()


async def name_taken(
    session_factory: async_sessionmaker[AsyncSession], user_id: UUID, name: str
) -> bool:
    async with SqlAlchemyAccountsUnitOfWork(session_factory, user_id) as uow:
        return await uow.accounts.name_taken(name)


async def test_name_is_taken_ignoring_case_and_only_for_its_owner(
    session_factory: async_sessionmaker[AsyncSession], new_user: Callable[[], Awaitable[UUID]]
) -> None:
    owner, other = await new_user(), await new_user()
    await save(session_factory, galicia(owner))

    assert await name_taken(session_factory, owner, "  GALICIA ")
    assert not await name_taken(session_factory, other, "Galicia")


async def test_archived_accounts_free_their_name(
    session_factory: async_sessionmaker[AsyncSession], new_user: Callable[[], Awaitable[UUID]]
) -> None:
    owner = await new_user()
    await save(session_factory, galicia(owner, archived=True))

    assert not await name_taken(session_factory, owner, "Galicia")
    await save(session_factory, galicia(owner))


async def test_unique_index_blocks_simultaneous_duplicates(
    session_factory: async_sessionmaker[AsyncSession], new_user: Callable[[], Awaitable[UUID]]
) -> None:
    # Simula dos altas que pasaron a la vez la verificación del caso de uso.
    owner = await new_user()
    await save(session_factory, galicia(owner))

    with pytest.raises(AccountNameTakenError):
        await save(session_factory, galicia(owner, name="galicia"))
