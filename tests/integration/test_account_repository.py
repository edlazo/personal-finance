from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.modules.identity.domain.user import User
from app.modules.identity.infrastructure.persistence import SqlAlchemyIdentityUnitOfWork
from app.modules.ledger.domain.account import Account, AccountNameTakenError, AccountType
from app.modules.ledger.infrastructure.accounts import SqlAlchemyAccountsUnitOfWork
from app.shared.domain.errors import NotFoundError
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


def galicia_account(user_id: UUID, name: str = "Galicia", archived: bool = False) -> Account:
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
    await save(session_factory, galicia_account(owner))

    assert await name_taken(session_factory, owner, "  GALICIA ")
    assert not await name_taken(session_factory, other, "Galicia")


async def test_archived_accounts_free_their_name(
    session_factory: async_sessionmaker[AsyncSession], new_user: Callable[[], Awaitable[UUID]]
) -> None:
    owner = await new_user()
    await save(session_factory, galicia_account(owner, archived=True))

    assert not await name_taken(session_factory, owner, "Galicia")
    await save(session_factory, galicia_account(owner))


async def test_unique_index_blocks_simultaneous_duplicates(
    session_factory: async_sessionmaker[AsyncSession], new_user: Callable[[], Awaitable[UUID]]
) -> None:
    # Simula dos altas que pasaron a la vez la verificación del caso de uso.
    owner = await new_user()
    await save(session_factory, galicia_account(owner))

    with pytest.raises(AccountNameTakenError):
        await save(session_factory, galicia_account(owner, name="galicia"))


async def test_list_get_and_save_stay_within_the_owner(
    session_factory: async_sessionmaker[AsyncSession], new_user: Callable[[], Awaitable[UUID]]
) -> None:
    owner, other = await new_user(), await new_user()
    galicia, santander = galicia_account(owner), galicia_account(owner, name="Santander")
    for account in (galicia, santander):
        await save(session_factory, account)

    async with SqlAlchemyAccountsUnitOfWork(session_factory, owner) as uow:
        santander.archive()
        await uow.accounts.save(santander)
        await uow.commit()
    async with SqlAlchemyAccountsUnitOfWork(session_factory, owner) as uow:
        assert [a.name for a in await uow.accounts.list_accounts(include_archived=False)] == [
            "Galicia"
        ]
        assert len(await uow.accounts.list_accounts(include_archived=True)) == 2
        assert (await uow.accounts.get_account(santander.id)).archived_at is not None
    async with SqlAlchemyAccountsUnitOfWork(session_factory, other) as uow:
        with pytest.raises(NotFoundError):
            await uow.accounts.get_account(galicia.id)


async def test_unique_index_blocks_a_rename_to_a_taken_name(
    session_factory: async_sessionmaker[AsyncSession], new_user: Callable[[], Awaitable[UUID]]
) -> None:
    owner = await new_user()
    galicia, santander = galicia_account(owner), galicia_account(owner, name="Santander")
    for account in (galicia, santander):
        await save(session_factory, account)

    santander.edit(name="GALICIA")
    with pytest.raises(AccountNameTakenError):
        async with SqlAlchemyAccountsUnitOfWork(session_factory, owner) as uow:
            await uow.accounts.save(santander)
