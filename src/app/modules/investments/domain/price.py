"""Precios de los instrumentos: nunca se pisan, cada carga es una fila del historial."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from app.modules.investments.domain.instrument import Instrument, Market
from app.modules.investments.domain.trade import PRICE_PRECISION, InvalidTradeError
from app.shared.domain.money import Currency


class PriceSource(StrEnum):
    MANUAL = "MANUAL"
    API = "API"


@dataclass
class InstrumentPrice:
    """Por unidad (cada 100 VN en bonos y ONs), en la moneda del instrumento."""

    user_id: UUID
    instrument_id: UUID
    price: Decimal
    date: date
    source: PriceSource = PriceSource.MANUAL
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.price <= 0 or self.price != self.price.quantize(PRICE_PRECISION):
            raise InvalidTradeError("El precio tiene que ser mayor a cero y con menos decimales")


class PriceRepository(Protocol):
    async def add(self, price: InstrumentPrice) -> None: ...

    async def latest_prices(self) -> dict[UUID, InstrumentPrice]:
        """Decisión del PO: el automático (API) gana al manual aunque sea más viejo; entre los
        de la misma fuente, el de fecha más reciente y después el último cargado."""
        ...


class PriceProvider(Protocol):
    async def prices(self, tickers: set[str]) -> dict[str, dict[Currency, Decimal]]:
        """Precio actual de cada ticker en las monedas que haya; los desconocidos no vienen."""
        ...


class MarketPriceProvider(Protocol):
    async def market_prices(self) -> dict[tuple[Market, str], dict[Currency, Decimal]]:
        """Precio actual por mercado y ticker, en la moneda en que cotiza."""
        ...


class CryptoPriceStore(Protocol):
    """Para los jobs: ve los instrumentos de todos los usuarios."""

    async def list_crypto(self) -> list[Instrument]: ...

    async def list_listed(self) -> list[Instrument]:
        """Los que cotizan en BYMA, NYSE o NASDAQ."""
        ...

    async def add(self, price: InstrumentPrice) -> None: ...
