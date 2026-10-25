"""Caso de uso: guardar las cotizaciones de la fuente automática."""

from dataclasses import dataclass

from app.modules.fx.application.register_rate import FxUnitOfWork
from app.modules.fx.domain.rate import ExchangeRateProvider


@dataclass(frozen=True)
class SyncRates:
    """El UoW tiene que ser sin usuario: así `latest()` ve solo las de la API."""

    uow: FxUnitOfWork
    provider: ExchangeRateProvider

    async def __call__(self) -> int:
        fetched = await self.provider.fetch()
        async with self.uow:
            last = {rate.type: rate.quoted_at for rate in await self.uow.rates.latest()}
            # La fuente repite el valor hasta que cambia: solo se guarda lo nuevo.
            new = [r for r in fetched if r.type not in last or r.quoted_at > last[r.type]]
            for rate in new:
                await self.uow.rates.add(rate)
            await self.uow.commit()
        return len(new)
