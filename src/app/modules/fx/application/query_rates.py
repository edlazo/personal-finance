"""Casos de uso: consultar las cotizaciones actuales y el historial."""

from dataclasses import dataclass
from datetime import datetime

from app.modules.fx.application.register_rate import FxUnitOfWork
from app.modules.fx.domain.rate import ExchangeRate
from app.shared.domain.rates import RateType


@dataclass(frozen=True)
class LatestRates:
    uow: FxUnitOfWork

    async def __call__(self) -> list[ExchangeRate]:
        async with self.uow:
            return await self.uow.rates.latest()


@dataclass(frozen=True)
class RateHistory:
    uow: FxUnitOfWork

    async def __call__(
        self,
        rate_type: RateType | None = None,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[ExchangeRate]:
        async with self.uow:
            return await self.uow.rates.history(rate_type, since=since, until=until)
