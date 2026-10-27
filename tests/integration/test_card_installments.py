from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.cards.application.manage_cards import (
    CreateCard,
    PendingInstallments,
    RegisterPurchase,
)
from app.modules.cards.domain.card import CardNetwork, CreditCard
from app.modules.cards.domain.purchase import CardPurchase
from app.modules.cards.infrastructure.persistence import SqlAlchemyCardsUnitOfWork
from app.modules.identity.domain.user import User
from app.modules.identity.infrastructure.persistence import SqlAlchemyIdentityUnitOfWork
from app.shared.domain.money import Currency
from app.shared.infrastructure.database import create_session_factory

pytestmark = pytest.mark.integration


async def test_installments_are_stored_and_read_by_due_date(
    migrated_database_url: str, engine: AsyncEngine
) -> None:
    factory = create_session_factory(engine)
    user = User(email=f"cuotas-{uuid4().hex[:8]}@example.com", name="Ana", password_hash="h")
    async with SqlAlchemyIdentityUnitOfWork(factory) as identity:
        await identity.users.add(user)
        await identity.commit()
    card = CreditCard(user.id, "Visa", CardNetwork.VISA, 25, 5, dual_currency=True)
    await CreateCard(SqlAlchemyCardsUnitOfWork(factory, user.id))(card)

    for description, amount, currency, count in (
        ("Heladera", "900000", Currency.ARS, 3),
        ("Spotify", "12.99", Currency.USD, 1),
    ):
        purchase = CardPurchase(
            user.id, card.id, description, Decimal(amount), currency, count, date(2026, 10, 20)
        )
        await RegisterPurchase(SqlAlchemyCardsUnitOfWork(factory, user.id))(purchase)
    pending = await PendingInstallments(SqlAlchemyCardsUnitOfWork(factory, user.id))(
        card.id, today=date(2026, 11, 6)
    )

    assert [(i.description, i.number, i.count, i.amount, i.due_date) for i in pending] == [
        ("Heladera", 2, 3, Decimal("300000.00"), date(2026, 12, 5)),
        ("Heladera", 3, 3, Decimal("300000.00"), date(2027, 1, 5)),
    ]
