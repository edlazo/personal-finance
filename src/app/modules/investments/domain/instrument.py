"""Instrumentos financieros del catálogo de cada usuario."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from app.shared.domain.errors import ConflictError, DomainError
from app.shared.domain.money import Currency


class InstrumentType(StrEnum):
    STOCK = "STOCK"
    CEDEAR = "CEDEAR"
    BOND = "BOND"
    ETF = "ETF"
    ON = "ON"
    CRYPTO = "CRYPTO"


class Market(StrEnum):
    BYMA = "BYMA"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    CRYPTO = "CRYPTO"


class InvalidInstrumentError(DomainError):
    pass


class InstrumentTickerTakenError(ConflictError):
    def __init__(self) -> None:
        super().__init__("Ya tenés un instrumento con ese ticker en ese mercado")


@dataclass
class Instrument:
    """Decisión del PO: el catálogo es de cada usuario; el ticker es único por mercado."""

    user_id: UUID
    ticker: str
    name: str
    type: InstrumentType
    market: Market
    # Moneda en la que cotiza.
    currency: Currency
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.ticker = self.ticker.strip().upper()
        self.name = self.name.strip()
        if not self.ticker or not self.name:
            raise InvalidInstrumentError("El ticker y el nombre son obligatorios")

    @property
    def quote_unit(self) -> int:
        """Bonos y ONs cotizan cada 100 de valor nominal; el resto, por unidad."""
        return 100 if self.type in (InstrumentType.BOND, InstrumentType.ON) else 1


class InstrumentRepository(Protocol):
    async def ticker_taken(self, ticker: str, market: Market) -> bool: ...

    async def add(self, instrument: Instrument) -> None: ...

    async def list_instruments(self) -> list[Instrument]: ...

    async def get_instrument(self, instrument_id: UUID) -> Instrument: ...
