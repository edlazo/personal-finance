"""Caso de uso: guardar los precios de BYMA, NYSE y NASDAQ de una fuente automática (data912)."""

from dataclasses import dataclass
from datetime import date

from app.modules.investments.application.sync_crypto_prices import PriceSyncUnitOfWork
from app.modules.investments.domain.price import (
    InstrumentPrice,
    MarketPriceProvider,
    PriceSource,
)
from app.modules.investments.domain.trade import PRICE_PRECISION


@dataclass(frozen=True)
class SyncMarketPrices:
    uow: PriceSyncUnitOfWork
    provider: MarketPriceProvider

    async def __call__(self, on: date) -> int:
        """Guarda un precio por instrumento de cada usuario, si cotiza en su moneda."""
        async with self.uow:
            instruments = await self.uow.store.list_listed()
        if not instruments:
            return 0
        quotes = await self.provider.market_prices()
        saved = 0
        async with self.uow:
            for instrument in instruments:
                key = (instrument.market, instrument.ticker)
                price = quotes.get(key, {}).get(instrument.currency)
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
