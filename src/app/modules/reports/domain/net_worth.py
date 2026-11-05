"""El reporte de patrimonio neto: totales por grupo y moneda (US-047)."""

from dataclasses import dataclass
from decimal import Decimal

from app.shared.domain.money import Currency
from app.shared.domain.net_worth import NetWorthGroup
from app.shared.domain.rates import RateType


@dataclass(frozen=True)
class GroupTotal:
    group: NetWorthGroup
    # En la moneda de origen.
    by_currency: dict[Currency, Decimal]
    # Convertido a cada moneda pedida.
    total: dict[Currency, Decimal]


@dataclass(frozen=True)
class NetWorthReport:
    rate_type: RateType
    groups: list[GroupTotal]
    assets: dict[Currency, Decimal]
    liabilities: dict[Currency, Decimal]
    net_worth: dict[Currency, Decimal]
