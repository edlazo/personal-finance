from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.cards.application.manage_cards import (
    CreateCard,
    PendingInstallments,
    RegisterPayment,
    RegisterPurchase,
)
from app.modules.cards.domain.card import CardNetwork, CreditCard
from app.modules.cards.domain.purchase import CardPurchase
from app.modules.cards.infrastructure.persistence import SqlAlchemyCardsUnitOfWork
from app.modules.identity.domain.user import User
from app.modules.identity.infrastructure.persistence import SqlAlchemyIdentityUnitOfWork
from app.modules.ledger.application.create_account import CreateAccount
from app.modules.ledger.domain.account import AccountType, NegativeBalanceError
from app.modules.ledger.infrastructure.accounts import SqlAlchemyAccountsUnitOfWork
from app.modules.ledger.infrastructure.cash_movements import LedgerCashMovements
from app.shared.domain.money import Currency
from app.shared.infrastructure.database import create_session_factory

pytestmark = pytest.mark.integration
ARS = Currency.ARS


async def test_installments_payments_and_pending_ones_are_stored(
    migrated_database_url: str, engine: AsyncEngine
) -> None:
    factory = create_session_factory(engine)
    user = User(email=f"cuotas-{uuid4().hex[:8]}@example.com", name="Ana", password_hash="h")
    async with SqlAlchemyIdentityUnitOfWork(factory) as identity:
        await identity.users.add(user)
        await identity.commit()
    account = await CreateAccount(SqlAlchemyAccountsUnitOfWork(factory, user.id))(
        user_id=user.id,
        name="Galicia",
        account_type=AccountType.SAVINGS,
        currency=Currency.ARS,
        initial_balance=Decimal("400000"),
    )

    def uow() -> SqlAlchemyCardsUnitOfWork:
        return SqlAlchemyCardsUnitOfWork(factory, user.id, LedgerCashMovements)

    async def pay(month: int, on: date) -> None:
        amount = Decimal("300000")
        await RegisterPayment(uow())(
            user.id, card.id, 2026, month, account_id=account.id, amount=amount, currency=ARS, on=on
        )

    card = CreditCard(user.id, "Visa", CardNetwork.VISA, 25, 5, dual_currency=True)
    await CreateCard(uow())(card)
    for description, amount, currency, count in (
        ("Heladera", "900000", Currency.ARS, 3),
        ("Spotify", "12.99", Currency.USD, 1),
    ):
        purchase = CardPurchase(
            user.id, card.id, description, Decimal(amount), currency, count, date(2026, 10, 20)
        )
        await RegisterPurchase(uow())(purchase)
    await pay(10, date(2026, 11, 2))
    pending = await PendingInstallments(uow())(card.id)

    # La cuota 1 de la heladera está pagada; los dólares de octubre, no.
    assert [(i.description, i.number, i.count, i.amount, i.due_date) for i in pending] == [
        ("Spotify", 1, 1, Decimal("12.99"), date(2026, 11, 5)),
        ("Heladera", 2, 3, Decimal("300000.00"), date(2026, 12, 5)),
        ("Heladera", 3, 3, Decimal("300000.00"), date(2027, 1, 5)),
    ]
    with pytest.raises(NegativeBalanceError):
        await pay(11, date(2026, 11, 3))
