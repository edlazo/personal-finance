"""Tabla, repositorio y Unit of Work de los instrumentos."""

from datetime import datetime
from typing import Self
from uuid import UUID

from sqlalchemy import DateTime, Enum, String, UniqueConstraint, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.investments.domain.instrument import (
    Instrument,
    InstrumentTickerTakenError,
    InstrumentType,
    Market,
)
from app.shared.domain.money import Currency
from app.shared.infrastructure.database import Base
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.infrastructure.user_scoped import UserOwnedMixin, UserScopedRepository


class InstrumentModel(UserOwnedMixin, Base):
    __tablename__ = "instruments"
    # El ticker se guarda en mayúsculas: único por mercado dentro de cada usuario.
    __table_args__ = (UniqueConstraint("user_id", "market", "ticker"),)

    ticker: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[InstrumentType] = mapped_column(
        Enum(InstrumentType, name="instrument_type", native_enum=False, length=10)
    )
    market: Mapped[Market] = mapped_column(
        Enum(Market, name="market", native_enum=False, length=10)
    )
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency", native_enum=False, length=3)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def _to_domain(model: InstrumentModel) -> Instrument:
    return Instrument(
        id=model.id,
        user_id=model.user_id,
        ticker=model.ticker,
        name=model.name,
        type=model.type,
        market=model.market,
        currency=model.currency,
        created_at=model.created_at,
    )


class SqlAlchemyInstrumentRepository(UserScopedRepository[InstrumentModel]):
    model = InstrumentModel

    async def ticker_taken(self, ticker: str, market: Market) -> bool:
        query = self.scoped().where(
            InstrumentModel.ticker == ticker, InstrumentModel.market == market
        )
        return await self.session.scalar(select(query.exists())) or False

    async def add(self, instrument: Instrument) -> None:
        self.session.add(
            InstrumentModel(
                id=instrument.id,
                user_id=instrument.user_id,
                ticker=instrument.ticker,
                name=instrument.name,
                type=instrument.type,
                market=instrument.market,
                currency=instrument.currency,
                created_at=instrument.created_at,
            )
        )
        try:
            await self.session.flush()
        except IntegrityError as exc:
            # Dos altas simultáneas del mismo ticker: las frena la restricción única.
            raise InstrumentTickerTakenError from exc

    async def list_instruments(self) -> list[Instrument]:
        query = self.scoped().order_by(InstrumentModel.market, InstrumentModel.ticker)
        return [_to_domain(model) for model in await self.session.scalars(query)]

    async def get_instrument(self, instrument_id: UUID) -> Instrument:
        return _to_domain(await self.get(instrument_id))


class SqlAlchemyInvestmentsUnitOfWork(SqlAlchemyUnitOfWork):
    instruments: SqlAlchemyInstrumentRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], user_id: UUID) -> None:
        super().__init__(session_factory)
        self._user_id = user_id

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self.instruments = SqlAlchemyInstrumentRepository(self.session, self._user_id)
        return self
