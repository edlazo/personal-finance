"""Servicio: convertir montos entre ARS y USD con una cotización guardada."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.modules.fx.application.register_rate import FxUnitOfWork
from app.shared.domain.money import Currency
from app.shared.domain.rates import RateNotAvailableError, RateType


@dataclass(frozen=True)
class CurrencyConverter:
    """Implementa `MoneyConverter` (app.shared) con las cotizaciones que ve el usuario del UoW."""

    uow: FxUnitOfWork

    async def convert(
        self,
        amount: Decimal,
        source: Currency,
        target: Currency,
        *,
        rate_type: RateType,
        at: datetime,
    ) -> Decimal:
        if source is target:
            return amount
        async with self.uow:
            rate = await self.uow.rates.rate_at(rate_type, at)
        if rate is None:
            raise RateNotAvailableError(rate_type, at)
        return rate.convert(amount, source, target)
