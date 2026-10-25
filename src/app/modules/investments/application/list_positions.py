"""Caso de uso: mis posiciones, valuadas en la moneda del instrumento y en ARS y USD."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.modules.investments.application.register_trade import TradesUnitOfWork
from app.modules.investments.domain.position import Position, build_positions
from app.shared.domain.money import Currency
from app.shared.domain.rates import MoneyConverter, RatePreference, RateType


@dataclass(frozen=True)
class ValuedPosition:
    position: Position
    valuation_ars: Decimal
    valuation_usd: Decimal


@dataclass(frozen=True)
class ListPositions:
    uow: TradesUnitOfWork
    converter: MoneyConverter
    preference: RatePreference

    async def __call__(
        self, user_id: UUID, *, rate_type: RateType | None = None
    ) -> tuple[RateType, list[ValuedPosition]]:
        rate_type = rate_type or await self.preference.default_rate_type(user_id)
        async with self.uow:
            instruments = {i.id: i for i in await self.uow.instruments.list_instruments()}
            trades = await self.uow.trades.list_trades()
        at = datetime.now(UTC)

        async def convert(position: Position, target: Currency) -> Decimal:
            return await self.converter.convert(
                position.valuation, position.instrument.currency, target, rate_type=rate_type, at=at
            )

        valued = [
            ValuedPosition(p, await convert(p, Currency.ARS), await convert(p, Currency.USD))
            for p in build_positions(trades, instruments)
        ]
        return rate_type, valued
