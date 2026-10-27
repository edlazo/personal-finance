"""Caso de uso: guardar los precios de cripto de una fuente automática (CoinGecko)."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from app.modules.investments.domain.price import (
    CryptoPriceStore,
    InstrumentPrice,
    PriceProvider,
    PriceSource,
)
from app.modules.investments.domain.trade import PRICE_PRECISION
from app.shared.application.unit_of_work import UnitOfWork


class PriceSyncUnitOfWork(UnitOfWork, Protocol):
    @property
    def store(self) -> CryptoPriceStore: ...


@dataclass(frozen=True)
class SyncCryptoPrices:
    uow: PriceSyncUnitOfWork
    provider: PriceProvider

    async def __call__(self, on: date) -> int:
        """Guarda un precio por instrumento cripto de cada usuario, en su moneda."""
        async with self.uow:
            instruments = await self.uow.store.list_crypto()
        if not instruments:
            return 0
        # Una sola llamada para todos los tickers, sin una sesión abierta mientras espera.
        quotes = await self.provider.prices({i.ticker for i in instruments})
        saved = 0
        async with self.uow:
            for instrument in instruments:
                price = quotes.get(instrument.ticker, {}).get(instrument.currency)
                if price is None:
                    continue
                entry = InstrumentPrice(
                    instrument.user_id,
                    instrument.id,
                    price.quantize(PRICE_PRECISION),
                    on,
                    PriceSource.API,
                )
                await self.uow.store.add(entry)
                saved += 1
            await self.uow.commit()
        return saved
