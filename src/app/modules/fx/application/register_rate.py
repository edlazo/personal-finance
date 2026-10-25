"""Caso de uso: cargar una cotización a mano."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.modules.fx.domain.rate import ExchangeRate, ExchangeRateRepository, RateSource
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.rates import RateType


class FxUnitOfWork(UnitOfWork, Protocol):
    @property
    def rates(self) -> ExchangeRateRepository: ...


@dataclass(frozen=True)
class RegisterManualRate:
    uow: FxUnitOfWork

    async def __call__(
        self,
        user_id: UUID,
        *,
        rate_type: RateType,
        buy: Decimal,
        sell: Decimal,
        quoted_at: datetime,
    ) -> ExchangeRate:
        rate = ExchangeRate(rate_type, buy, sell, quoted_at, RateSource.MANUAL, user_id=user_id)
        async with self.uow:
            await self.uow.rates.add(rate)
            await self.uow.commit()
        return rate
