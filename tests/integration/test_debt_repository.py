from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.debts.application.manage_debts import CreateDebt, GetDebt, ListDebts
from app.modules.debts.domain.debt import Debt, DebtDirection
from app.modules.debts.infrastructure.persistence import SqlAlchemyDebtsUnitOfWork
from app.modules.identity.domain.user import User
from app.modules.identity.infrastructure.persistence import SqlAlchemyIdentityUnitOfWork
from app.shared.domain.errors import NotFoundError
from app.shared.domain.money import Currency
from app.shared.infrastructure.database import create_session_factory

pytestmark = pytest.mark.integration


async def test_debts_and_their_schedule_are_stored_per_user(
    migrated_database_url: str, engine: AsyncEngine
) -> None:
    factory = create_session_factory(engine)

    async def new_user() -> UUID:
        user = User(email=f"deudas-{uuid4().hex[:8]}@example.com", name="Ana", password_hash="h")
        async with SqlAlchemyIdentityUnitOfWork(factory) as uow:
            await uow.users.add(user)
            await uow.commit()
        return user.id

    ana, beto = await new_user(), await new_user()
    loan = Debt(
        ana,
        "Banco",
        DebtDirection.OWED,
        Currency.USD,
        Decimal("5000"),
        24,
        date(2027, 1, 10),
        Decimal("12.5"),
    )
    schedule = await CreateDebt(SqlAlchemyDebtsUnitOfWork(factory, ana))(loan)

    assert await GetDebt(SqlAlchemyDebtsUnitOfWork(factory, ana))(loan.id) == (loan, schedule)
    assert await ListDebts(SqlAlchemyDebtsUnitOfWork(factory, beto))() == []
    with pytest.raises(NotFoundError):
        await GetDebt(SqlAlchemyDebtsUnitOfWork(factory, beto))(loan.id)
