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


@dataclass(frozen=True)
class ListPositions:
    uow: PositionsUnitOfWork
    converter: MoneyConverter
    preference: RatePreference

    async def __call__(
        self, user_id: UUID, *, rate_type: RateType | None = None
    ) -> tuple[RateType, list[ValuedPosition]]:
        rate_type = rate_type or await self.preference.default_rate_type(user_id)
        async with self.uow:
            instruments = {i.id: i for i in await self.uow.instruments.list_instruments()}
            trades = await self.uow.trades.list_trades()
            prices = await self.uow.prices.latest_prices()
            events = await self.uow.events.list_events()
            snapshots = await self.uow.snapshots.list_snapshots()
            linked = await self.uow.links.linked_account(Broker.IOL)
        at = datetime.now(UTC)
        # En la cuenta vinculada manda el portafolio de IOL (aunque esté vacío), no las operaciones
        # cargadas antes; la foto de una cuenta que se desvinculó ya no cuenta.
        trades = [t for t in trades if t.account_id != linked]
        events = [e for e in events if e.account_id != linked]
        snapshots = [s for s in snapshots if s.account_id == linked]
        positions = sorted(
            build_positions(trades, instruments, prices, events)
            + snapshot_positions(snapshots, instruments),
            key=lambda p: (p.instrument.ticker, str(p.account_id)),
        )

        async def convert(position: Position, target: Currency) -> Decimal:
            return await self.converter.convert(
                position.valuation, position.instrument.currency, target, rate_type=rate_type, at=at
            )

        valued = [
            ValuedPosition(p, await convert(p, Currency.ARS), await convert(p, Currency.USD))
            for p in positions
        ]
        return rate_type, valued
