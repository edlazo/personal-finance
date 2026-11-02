"""Tablas, repositorio y Unit of Work de las deudas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Self
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, SmallInteger, String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.debts.domain.debt import Debt, DebtDirection, DebtInstallment
from app.shared.domain.money import Currency
from app.shared.infrastructure.database import Base
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.infrastructure.user_scoped import UserOwnedMixin, UserScopedRepository


class DebtModel(UserOwnedMixin, Base):
    __tablename__ = "debts"

    counterparty: Mapped[str] = mapped_column(String(100))
    direction: Mapped[DebtDirection] = mapped_column(
        Enum(DebtDirection, name="debt_direction", native_enum=False, length=4)
    )
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency", native_enum=False, length=3)
    )
    principal: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    installments: Mapped[int] = mapped_column(SmallInteger)
    start_date: Mapped[date] = mapped_column(Date)
    annual_rate: Mapped[Decimal | None] = mapped_column(Numeric(9, 4))
    fixed_installment: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DebtInstallmentModel(UserOwnedMixin, Base):
    """Se guardan al registrar la deuda: el cronograma no cambia después."""

    __tablename__ = "debt_installments"

    debt_id: Mapped[UUID] = mapped_column(ForeignKey("debts.id", ondelete="CASCADE"), index=True)
    number: Mapped[int] = mapped_column(SmallInteger)
    due_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    principal: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    interest: Mapped[Decimal] = mapped_column(Numeric(20, 2))


def _to_domain(m: DebtModel) -> Debt:
    return Debt(
        m.user_id,
        m.counterparty,
        m.direction,
        m.currency,
        m.principal,
        m.installments,
        m.start_date,
        m.annual_rate,
        m.fixed_installment,
        m.id,
        m.created_at,
    )


class SqlAlchemyDebtRepository(UserScopedRepository[DebtModel]):
    model = DebtModel

    async def add(self, debt: Debt, installments: list[DebtInstallment]) -> None:
        self.session.add(
            DebtModel(
                id=debt.id,
                user_id=debt.user_id,
                counterparty=debt.counterparty,
                direction=debt.direction,
                currency=debt.currency,
                principal=debt.principal,
                installments=debt.installments,
                start_date=debt.start_date,
                annual_rate=debt.annual_rate,
                fixed_installment=debt.fixed_installment,
                created_at=debt.created_at,
            )
        )
        # Sin relationship, SQLAlchemy no ordena los inserts: la deuda va antes que sus cuotas.
        await self.session.flush()
        self.session.add_all(
            DebtInstallmentModel(
                id=uuid4(),
                user_id=debt.user_id,
                debt_id=debt.id,
                number=i.number,
                due_date=i.due_date,
                amount=i.amount,
                principal=i.principal,
                interest=i.interest,
            )
            for i in installments
        )
        await self.session.flush()

    async def list_debts(self) -> list[Debt]:
        query = self.scoped().order_by(DebtModel.start_date, DebtModel.created_at)
        return [_to_domain(m) for m in await self.session.scalars(query)]

    async def get_debt(self, debt_id: UUID) -> Debt:
        return _to_domain(await self.get(debt_id))

    async def installments(self, debt_id: UUID) -> list[DebtInstallment]:
        m = DebtInstallmentModel
        query = select(m).where(m.user_id == self.user_id, m.debt_id == debt_id).order_by(m.number)
        return [
            DebtInstallment(i.number, i.due_date, i.amount, i.principal, i.interest)
            for i in await self.session.scalars(query)
        ]


class SqlAlchemyDebtsUnitOfWork(SqlAlchemyUnitOfWork):
    debts: SqlAlchemyDebtRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], user_id: UUID) -> None:
        super().__init__(session_factory)
        self._user_id = user_id

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self.debts = SqlAlchemyDebtRepository(self.session, self._user_id)
        return self
