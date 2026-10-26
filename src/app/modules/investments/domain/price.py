"""Precios de los instrumentos: nunca se pisan, cada carga es una fila del historial."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from app.modules.investments.domain.trade import PRICE_PRECISION, InvalidTradeError


class PriceSource(StrEnum):
    MANUAL = "MANUAL"


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
        """El precio más reciente de cada instrumento, por fecha y después por carga."""
        ...
