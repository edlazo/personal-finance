"""Cotización del dólar: compra y venta en ARS de un tipo, en un momento."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from app.shared.domain.errors import DomainError
from app.shared.domain.rates import RateType

# NUMERIC(28,10): hasta 10 decimales.
PRECISION = Decimal("1e-10")


class RateSource(StrEnum):
    API = "API"
    MANUAL = "MANUAL"


class InvalidRateError(DomainError):
    pass


@dataclass
class ExchangeRate:
    """Nunca se edita: cada valor nuevo es otra fila, así queda el historial completo."""

    type: RateType
    buy: Decimal
    sell: Decimal
    quoted_at: datetime
    source: RateSource
    # Las de la API son de todos (None); las manuales, del usuario que las cargó.
    user_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        for price in (self.buy, self.sell):
            if price <= 0:
                raise InvalidRateError("La compra y la venta tienen que ser mayores a cero")
            if price != price.quantize(PRECISION):
                raise InvalidRateError("La cotización admite hasta 10 decimales")
        if self.quoted_at.tzinfo is None:
            raise InvalidRateError("La fecha y hora de la cotización necesita zona horaria")
        if (self.source is RateSource.MANUAL) != (self.user_id is not None):
            raise InvalidRateError("Solo las cotizaciones manuales tienen dueño")


class ExchangeRateRepository(Protocol):
    async def add(self, rate: ExchangeRate) -> None: ...
