"""Tabla, repositorio y Unit of Work de las cotizaciones."""

from datetime import datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.fx.domain.rate import ExchangeRate, RateSource
from app.shared.domain.rates import RateType
from app.shared.infrastructure.database import Base
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


class ExchangeRateModel(Base):
    __tablename__ = "fx_rates"
    # La última de cada tipo y el historial por fechas (PF-40) se buscan por tipo y momento.
    __table_args__ = (Index("ix_fx_rates_type_quoted_at", "type", "quoted_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    # NULL: cotización de la API, visible para todos.
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[RateType] = mapped_column(
        Enum(RateType, name="type", native_enum=False, create_constraint=True, length=10)
    )
    buy: Mapped[Decimal] = mapped_column(Numeric(28, 10))
    sell: Mapped[Decimal] = mapped_column(Numeric(28, 10))
    quoted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[RateSource] = mapped_column(
        Enum(RateSource, name="source", native_enum=False, create_constraint=True, length=10)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SqlAlchemyExchangeRateRepository:
    def __init__(self, session: AsyncSession, user_id: UUID) -> None:
        self.session = session
        self.user_id = user_id

    async def add(self, rate: ExchangeRate) -> None:
        self.session.add(
            ExchangeRateModel(
                id=rate.id,
                user_id=rate.user_id,
                type=rate.type,
                buy=rate.buy,
                sell=rate.sell,
                quoted_at=rate.quoted_at,
                source=rate.source,
                created_at=rate.created_at,
            )
        )
        await self.session.flush()


class SqlAlchemyFxUnitOfWork(SqlAlchemyUnitOfWork):
    rates: SqlAlchemyExchangeRateRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], user_id: UUID) -> None:
        super().__init__(session_factory)
        self._user_id = user_id

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self.rates = SqlAlchemyExchangeRateRepository(self.session, self._user_id)
        return self
