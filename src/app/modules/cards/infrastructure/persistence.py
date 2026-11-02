"""Tabla, repositorio y Unit of Work de las tarjetas de crédito."""

from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from typing import Self
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import ColumnElement

from app.modules.cards.domain.card import CardNetwork, CreditCard
from app.modules.cards.domain.payment import CardPayment
from app.modules.cards.domain.purchase import CardPurchase, Installment
from app.shared.domain.cash import CashMovements
from app.shared.domain.money import Currency
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


class CardPurchaseModel(UserOwnedMixin, Base):
    __tablename__ = "card_purchases"

    card_id: Mapped[UUID] = mapped_column(ForeignKey("credit_cards.id"), index=True)
    description: Mapped[str] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency", native_enum=False, length=3)
    )
    installments: Mapped[int] = mapped_column(SmallInteger)
    date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CardInstallmentModel(UserOwnedMixin, Base):
    """Se guardan al registrar la compra: el resumen de cada cuota no cambia después."""

    __tablename__ = "card_installments"

    purchase_id: Mapped[UUID] = mapped_column(
        ForeignKey("card_purchases.id", ondelete="CASCADE"), index=True
    )
    card_id: Mapped[UUID] = mapped_column(ForeignKey("credit_cards.id"), index=True)
    number: Mapped[int] = mapped_column(SmallInteger)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency", native_enum=False, length=3)
    )
    closing_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)


class SqlAlchemyPurchaseRepository(UserScopedRepository[CardPurchaseModel]):
    model = CardPurchaseModel

    async def add(self, purchase: CardPurchase, installments: list[Installment]) -> None:
        self.session.add(
            CardPurchaseModel(
                id=purchase.id,
                user_id=purchase.user_id,
                card_id=purchase.card_id,
                description=purchase.description,
                amount=purchase.amount,
                currency=purchase.currency,
                installments=purchase.installments,
                date=purchase.date,
                created_at=purchase.created_at,
            )
        )
        # Sin relationship, SQLAlchemy no ordena los inserts: la compra va antes que sus cuotas.
        await self.session.flush()
        self.session.add_all(
            CardInstallmentModel(
                id=uuid4(),
                user_id=purchase.user_id,
                purchase_id=purchase.id,
                card_id=purchase.card_id,
                number=i.number,
                amount=i.amount,
                currency=i.currency,
                closing_date=i.closing_date,
                due_date=i.due_date,
            )
            for i in installments
        )
        await self.session.flush()

    async def _installments(self, card_id: UUID, *where: ColumnElement[bool]) -> list[Installment]:
        i, p = CardInstallmentModel, CardPurchaseModel
        query = (
            select(i, p.description, p.installments, p.date)
            .join(p, p.id == i.purchase_id)
            .where(i.user_id == self.user_id, i.card_id == card_id, *where)
            .order_by(i.due_date, p.date, p.created_at, i.number)
        )
        return [
            Installment(
                m.purchase_id,
                description,
                m.number,
                count,
                m.amount,
                m.currency,
                m.closing_date,
                m.due_date,
                bought,
            )
            for m, description, count, bought in (await self.session.execute(query)).all()
        ]

    async def card_installments(self, card_id: UUID) -> list[Installment]:
        return await self._installments(card_id)

    async def statement_installments(self, card_id: UUID, closing_date: date) -> list[Installment]:
        return await self._installments(card_id, CardInstallmentModel.closing_date == closing_date)


class CardPaymentModel(UserOwnedMixin, Base):
    __tablename__ = "card_payments"

    card_id: Mapped[UUID] = mapped_column(ForeignKey("credit_cards.id"), index=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"))
    closing_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency", native_enum=False, length=3)
    )
    date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SqlAlchemyPaymentRepository(UserScopedRepository[CardPaymentModel]):
    model = CardPaymentModel

    async def add(self, payment: CardPayment) -> None:
        self.session.add(
            CardPaymentModel(
                id=payment.id,
                user_id=payment.user_id,
                card_id=payment.card_id,
                account_id=payment.account_id,
                closing_date=payment.closing_date,
                amount=payment.amount,
                currency=payment.currency,
                date=payment.date,
                created_at=payment.created_at,
            )
        )
        await self.session.flush()

    async def paid(self, card_id: UUID) -> dict[tuple[date, Currency], Decimal]:
        m = CardPaymentModel
        query = (
            select(m.closing_date, m.currency, func.sum(m.amount))
            .where(m.user_id == self.user_id, m.card_id == card_id)
            .group_by(m.closing_date, m.currency)
        )
        rows = (await self.session.execute(query)).all()
        return {(closing, currency): total for closing, currency, total in rows}


# Lo arma main.py con la implementación de ledger (contrato de app.shared).
CashMovementsFactory = Callable[[AsyncSession, UUID], CashMovements]


class SqlAlchemyCardsUnitOfWork(SqlAlchemyUnitOfWork):
    cards: SqlAlchemyCreditCardRepository
    purchases: SqlAlchemyPurchaseRepository
    payments: SqlAlchemyPaymentRepository
    cash: CashMovements

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        user_id: UUID,
        cash: CashMovementsFactory,
    ) -> None:
        super().__init__(session_factory)
        self._user_id = user_id
        self._cash = cash

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self.cards = SqlAlchemyCreditCardRepository(self.session, self._user_id)
        self.purchases = SqlAlchemyPurchaseRepository(self.session, self._user_id)
        self.payments = SqlAlchemyPaymentRepository(self.session, self._user_id)
        # Misma sesión: el pago y su movimiento en la cuenta se confirman juntos.
        self.cash = self._cash(self.session, self._user_id)
        return self
