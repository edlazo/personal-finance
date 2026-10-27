from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.cards.application.manage_cards import CreateCard, GetCard, ListCards
from app.modules.cards.domain.card import CardNetwork, CreditCard
from app.modules.cards.infrastructure.persistence import SqlAlchemyCardsUnitOfWork
from app.modules.identity.domain.user import User
from app.modules.identity.infrastructure.persistence import SqlAlchemyIdentityUnitOfWork
from app.shared.domain.errors import NotFoundError
from app.shared.infrastructure.database import create_session_factory

pytestmark = pytest.mark.integration


async def test_cards_are_stored_per_user(migrated_database_url: str, engine: AsyncEngine) -> None:
    factory = create_session_factory(engine)

    async def new_user() -> UUID:
        user = User(email=f"tarjetas-{uuid4().hex[:8]}@example.com", name="Ana", password_hash="h")
        async with SqlAlchemyIdentityUnitOfWork(factory) as uow:
            await uow.users.add(user)
            await uow.commit()
        return user.id

    ana, beto = await new_user(), await new_user()
    card = CreditCard(ana, "Visa", CardNetwork.VISA, 31, 10, True, Decimal("800000.50"))
    await CreateCard(SqlAlchemyCardsUnitOfWork(factory, ana))(card)

    assert await GetCard(SqlAlchemyCardsUnitOfWork(factory, ana))(card.id) == card
    assert await ListCards(SqlAlchemyCardsUnitOfWork(factory, beto))() == []
    with pytest.raises(NotFoundError):
        await GetCard(SqlAlchemyCardsUnitOfWork(factory, beto))(card.id)
