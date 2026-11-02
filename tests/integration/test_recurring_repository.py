from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.identity.domain.user import User
from app.modules.identity.infrastructure.persistence import SqlAlchemyIdentityUnitOfWork
from app.modules.ledger.application.manage_recurring import (
    CreateRecurring,
    DeleteRecurring,
    ListRecurring,
    UpdateRecurring,
)
from app.modules.ledger.domain.account import Account, AccountType
from app.modules.ledger.domain.category import Category, CategoryKind
from app.modules.ledger.domain.recurring import Frequency, RecurringRule
from app.modules.ledger.infrastructure.persistence import SqlAlchemyLedgerUnitOfWork
from app.shared.domain.money import Currency
from app.shared.infrastructure.database import create_session_factory

pytestmark = pytest.mark.integration


async def test_rules_are_stored_edited_and_deleted_per_user(
    migrated_database_url: str, engine: AsyncEngine
) -> None:
    factory = create_session_factory(engine)

    async def new_user() -> UUID:
        user = User(
            email=f"recurrentes-{uuid4().hex[:8]}@example.com", name="Ana", password_hash="h"
        )
        async with SqlAlchemyIdentityUnitOfWork(factory) as uow:
            await uow.users.add(user)
            await uow.commit()
        return user.id

    ana, beto = await new_user(), await new_user()
    account = Account(ana, "Galicia", AccountType.SAVINGS, Currency.ARS, Decimal("0"))
    salary = Category(ana, "Sueldo extra", CategoryKind.INCOME)
    async with SqlAlchemyLedgerUnitOfWork(factory, ana) as uow:
        await uow.accounts.add(account)
        await uow.categories.add(salary)
        await uow.commit()
    rule = RecurringRule(
        ana,
        account.id,
        CategoryKind.INCOME,
        Decimal("1500000"),
        salary.id,
        Frequency.MONTHLY,
        date(2026, 11, 5),
        description="Sueldo",
    )

    await CreateRecurring(SqlAlchemyLedgerUnitOfWork(factory, ana))(rule)
    paused = await UpdateRecurring(SqlAlchemyLedgerUnitOfWork(factory, ana))(
        rule.id, {"paused": True, "end_date": date(2027, 11, 5)}
    )

    assert await ListRecurring(SqlAlchemyLedgerUnitOfWork(factory, ana))() == [paused]
    assert await ListRecurring(SqlAlchemyLedgerUnitOfWork(factory, beto))() == []
    await DeleteRecurring(SqlAlchemyLedgerUnitOfWork(factory, ana))(rule.id)
    assert await ListRecurring(SqlAlchemyLedgerUnitOfWork(factory, ana))() == []
