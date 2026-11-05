"""Caso de uso: mis posiciones, valuadas en la moneda del instrumento y en ARS y USD."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.modules.investments.application.register_trade import TradesUnitOfWork
from app.modules.investments.domain.credentials import Broker
from app.modules.investments.domain.portfolio import SnapshotRepository
from app.modules.investments.domain.position import (
    Position,
    build_positions,
    snapshot_positions,
)
from app.modules.investments.domain.price import PriceRepository
from app.shared.domain.money import Currency
from app.shared.domain.net_worth import NetWorthGroup, NetWorthItem
from app.shared.domain.rates import MoneyConverter, RatePreference, RateType


class PositionsUnitOfWork(TradesUnitOfWork, Protocol):
    @property
    def prices(self) -> PriceRepository: ...

    @property
    def snapshots(self) -> SnapshotRepository: ...


@dataclass(frozen=True)
class ValuedPosition:
    position: Position
    valuation_ars: Decimal
    valuation_usd: Decimal


async def current_positions(uow: PositionsUnitOfWork) -> list[Position]:
    """Las posiciones del usuario, valuadas en la moneda de cada instrumento."""
    async with uow:
        instruments = {i.id: i for i in await uow.instruments.list_instruments()}
        trades = await uow.trades.list_trades()
        prices = await uow.prices.latest_prices()
        events = await uow.events.list_events()
        snapshots = await uow.snapshots.list_snapshots()
        linked = await uow.links.linked_account(Broker.IOL)
    # En la cuenta vinculada manda el portafolio de IOL (aunque esté vacío), no las operaciones
    # cargadas antes; la foto de una cuenta que se desvinculó ya no cuenta.
    trades = [t for t in trades if t.account_id != linked]
    events = [e for e in events if e.account_id != linked]
    snapshots = [s for s in snapshots if s.account_id == linked]
    return sorted(
        build_positions(trades, instruments, prices, events)
        + snapshot_positions(snapshots, instruments),
        key=lambda p: (p.instrument.ticker, str(p.account_id)),
    )


@dataclass(frozen=True)
class ListPositions:
    uow: PositionsUnitOfWork
    converter: MoneyConverter
    preference: RatePreference

    async def __call__(
        self, user_id: UUID, *, rate_type: RateType | None = None
    ) -> tuple[RateType, list[ValuedPosition]]:
        rate_type = rate_type or await self.preference.default_rate_type(user_id)
        positions = await current_positions(self.uow)
        at = datetime.now(UTC)

        async def convert(position: Position, target: Currency) -> Decimal:
            return await self.converter.convert(
                position.valuation, position.instrument.currency, target, rate_type=rate_type, at=at
            )

        valued = [
            ValuedPosition(p, await convert(p, Currency.ARS), await convert(p, Currency.USD))
            for p in positions
        ]
        return rate_type, valued


@dataclass(frozen=True)
class InvestmentsNetWorth:
    """Fuente del patrimonio: cada posición valuada, en la moneda del instrumento."""

    uow: PositionsUnitOfWork

    async def __call__(self) -> list[NetWorthItem]:
        return [
            NetWorthItem(NetWorthGroup.INVESTMENTS, p.instrument.currency, p.valuation)
            for p in await current_positions(self.uow)
        ]
