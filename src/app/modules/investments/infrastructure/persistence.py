"""Tabla, repositorio y Unit of Work de los instrumentos."""

from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    case,
    func,
    select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.investments.domain.instrument import (
    Instrument,
    InstrumentTickerTakenError,
    InstrumentType,
    Market,
)
from app.modules.investments.domain.trade import Trade, TradeSide
from app.shared.domain.cash import CashMovements
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


class TradeModel(UserOwnedMixin, Base):
    __tablename__ = "trades"

    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    instrument_id: Mapped[UUID] = mapped_column(ForeignKey("instruments.id"), index=True)
    side: Mapped[TradeSide] = mapped_column(
        Enum(TradeSide, name="trade_side", native_enum=False, length=4)
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 8))
    price: Mapped[Decimal] = mapped_column(Numeric(28, 10))
    fee: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    date: Mapped[date] = mapped_column(Date)
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


class SqlAlchemyTradeRepository(UserScopedRepository[TradeModel]):
    model = TradeModel

    async def add(self, trade: Trade) -> None:
        self.session.add(
            TradeModel(
                id=trade.id,
                user_id=trade.user_id,
                account_id=trade.account_id,
                instrument_id=trade.instrument_id,
                side=trade.side,
                quantity=trade.quantity,
                price=trade.price,
                fee=trade.fee,
                date=trade.date,
                created_at=trade.created_at,
            )
        )
        await self.session.flush()

    async def holding(self, account_id: UUID, instrument_id: UUID) -> Decimal:
        m = TradeModel
        signed = case((m.side == TradeSide.BUY, m.quantity), else_=-m.quantity)
        query = select(func.coalesce(func.sum(signed), 0)).where(
            m.user_id == self.user_id, m.account_id == account_id, m.instrument_id == instrument_id
        )
        return Decimal(await self.session.scalar(query) or 0)


# Lo arma main.py con la implementación de ledger (contrato de app.shared).
CashMovementsFactory = Callable[[AsyncSession, UUID], CashMovements]


class SqlAlchemyInvestmentsUnitOfWork(SqlAlchemyUnitOfWork):
    instruments: SqlAlchemyInstrumentRepository
    trades: SqlAlchemyTradeRepository
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
        self.instruments = SqlAlchemyInstrumentRepository(self.session, self._user_id)
        self.trades = SqlAlchemyTradeRepository(self.session, self._user_id)
        # Misma sesión: la operación y el movimiento de ledger se confirman juntos.
        self.cash = self._cash(self.session, self._user_id)
        return self
