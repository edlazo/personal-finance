"""Tipos de cotización del dólar y el contrato para convertir montos entre módulos."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from app.shared.domain.errors import DomainError
from app.shared.domain.money import Currency


class RateType(StrEnum):
    MEP = "MEP"
    OFICIAL = "OFICIAL"
    BLUE = "BLUE"
    CCL = "CCL"
    CRIPTO = "CRIPTO"


class RateNotAvailableError(DomainError):
    def __init__(self, rate_type: RateType, at: datetime) -> None:
        super().__init__(f"No hay cotización {rate_type} hasta el {at:%Y-%m-%d %H:%M}")


class MoneyConverter(Protocol):
    """Lo implementa fx; lo usan los módulos que muestran montos en otra moneda (US-025)."""

    async def convert(
        self,
        amount: Decimal,
        source: Currency,
        target: Currency,
        *,
        rate_type: RateType,
        at: datetime,
    ) -> Decimal:
        """Usa la última cotización del tipo hasta `at`; si no hay, RateNotAvailableError."""
        ...


class RatePreference(Protocol):
    """Lo implementa identity: la cotización que el usuario eligió por defecto."""

    async def default_rate_type(self, user_id: UUID) -> RateType: ...
