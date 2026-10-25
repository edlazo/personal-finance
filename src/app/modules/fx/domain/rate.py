"""Cotización del dólar: compra y venta en ARS de un tipo, en un momento."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from app.shared.domain.errors import DomainError
from app.shared.domain.money import Currency
from app.shared.domain.rates import RateType

# NUMERIC(28,10): hasta 10 decimales.
PRECISION = Decimal("1e-10")
CENTS = Decimal("0.01")


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

    def convert(self, amount: Decimal, source: Currency, target: Currency) -> Decimal:
        """ARS -> USD divide por la venta (lo que cuesta comprar un dólar); USD -> ARS
        multiplica por la compra (lo que pagan por venderlo). Redondea a centavos."""
        if source is target:
            return amount
        converted = amount / self.sell if source is Currency.ARS else amount * self.buy
        return converted.quantize(CENTS, ROUND_HALF_UP)


class ExchangeRateProvider(Protocol):
    async def fetch(self) -> list[ExchangeRate]:
        """Cotizaciones actuales de una fuente externa (`source=API`, sin dueño)."""
        ...


class ExchangeRateRepository(Protocol):
    """Las lecturas ven las cotizaciones de la API y las manuales del usuario actual."""

    async def add(self, rate: ExchangeRate) -> None: ...

    async def latest(self) -> list[ExchangeRate]:
        """La más reciente de cada tipo, ordenadas por tipo."""
        ...

    async def rate_at(self, rate_type: RateType, at: datetime) -> ExchangeRate | None:
        """La más reciente del tipo con fecha no posterior a `at`."""
        ...

    async def history(
        self, rate_type: RateType | None, *, since: datetime | None, until: datetime | None
    ) -> list[ExchangeRate]:
        """De la más reciente a la más vieja; `since` y `until` inclusive."""
        ...
