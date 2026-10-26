"""Tabla, repositorio y Unit of Work de las tarjetas de crédito."""

from datetime import datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, Numeric, SmallInteger, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.cards.domain.card import CardNetwork, CreditCard
from app.shared.infrastructure.database import Base
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.infrastructure.user_scoped import UserOwnedMixin, UserScopedRepository


class CreditCardModel(UserOwnedMixin, Base):
    __tablename__ = "credit_cards"

    name: Mapped[str] = mapped_column(String(100))
    network: Mapped[CardNetwork] = mapped_column(
        Enum(CardNetwork, name="card_network", native_enum=False, length=10)
    )
    closing_day: Mapped[int] = mapped_column(SmallInteger)
    due_day: Mapped[int] = mapped_column(SmallInteger)
    dual_currency: Mapped[bool] = mapped_column(Boolean)
    limit: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def _to_domain(m: CreditCardModel) -> CreditCard:
    return CreditCard(
        m.user_id,
        m.name,
        m.network,
        m.closing_day,
        m.due_day,
        m.dual_currency,
        m.limit,
        m.id,
        m.created_at,
    )


class SqlAlchemyCreditCardRepository(UserScopedRepository[CreditCardModel]):
    model = CreditCardModel

    async def add(self, card: CreditCard) -> None:
        self.session.add(
            CreditCardModel(
                id=card.id,
                user_id=card.user_id,
                name=card.name,
                network=card.network,
                closing_day=card.closing_day,
                due_day=card.due_day,
                dual_currency=card.dual_currency,
                limit=card.limit,
                created_at=card.created_at,
            )
        )
        await self.session.flush()

    async def list_cards(self) -> list[CreditCard]:
        query = self.scoped().order_by(CreditCardModel.name)
        return [_to_domain(m) for m in await self.session.scalars(query)]

    async def get_card(self, card_id: UUID) -> CreditCard:
        return _to_domain(await self.get(card_id))


class SqlAlchemyCardsUnitOfWork(SqlAlchemyUnitOfWork):
    cards: SqlAlchemyCreditCardRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], user_id: UUID) -> None:
        super().__init__(session_factory)
        self._user_id = user_id

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self.cards = SqlAlchemyCreditCardRepository(self.session, self._user_id)
        return self
