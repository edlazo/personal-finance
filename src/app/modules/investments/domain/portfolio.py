"""Foto del portafolio de un broker: en la cuenta vinculada, las tenencias salen de acá."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID, uuid4

from app.modules.investments.domain.credentials import Broker
from app.modules.investments.domain.instrument import InstrumentType, Market
from app.shared.domain.errors import DomainError
from app.shared.domain.money import Currency

# Token más portafolio: lo que gasta cada sincronización del cupo mensual de IOL.
CALLS_PER_SYNC = 2


@dataclass(frozen=True)
class HoldingSnapshot:
    """Una línea de la última foto. Los precios van como los informa el broker: por unidad, y
    cada 100 de valor nominal en bonos y ONs."""

    user_id: UUID
    account_id: UUID
    instrument_id: UUID
    quantity: Decimal
    # Precio promedio de compra (ppc) y último precio.
    average_price: Decimal
    last_price: Decimal
    taken_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)


class SnapshotRepository(Protocol):
    async def list_snapshots(self) -> list[HoldingSnapshot]:
        """La última foto de cada cuenta vinculada del usuario."""
        ...

    async def replace(self, snapshots: list[HoldingSnapshot]) -> None:
        """Reemplaza toda la foto del usuario (IOL es el único broker)."""
        ...


@dataclass(frozen=True)
class BrokerHolding:
    """Una tenencia como la informa el broker."""

    ticker: str
    name: str
    type: InstrumentType
    market: Market
    currency: Currency
    quantity: Decimal
    average_price: Decimal
    last_price: Decimal


class PortfolioClient(Protocol):
    async def portfolio(self, username: str, password: str) -> list[BrokerHolding]: ...


class CallBudgetExhaustedError(DomainError):
    pass


class CallBudgetRepository(Protocol):
    async def spend(self, broker: Broker, month: date, calls: int, limit: int) -> bool:
        """Suma las llamadas del mes si no pasan el límite; False si no hay cupo."""
        ...
