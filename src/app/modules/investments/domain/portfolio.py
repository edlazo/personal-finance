"""Foto del portafolio de un broker: en la cuenta vinculada, las tenencias salen de acá."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID, uuid4


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
