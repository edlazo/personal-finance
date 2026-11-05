"""Contrato para que el reporte de patrimonio neto lea lo que tiene y debe cada módulo (US-047)."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from app.shared.domain.money import Currency


class NetWorthGroup(StrEnum):
    # Decisión del PO: activos (cuentas, inversiones, préstamos otorgados) y pasivos.
    ACCOUNTS = "ACCOUNTS"
    INVESTMENTS = "INVESTMENTS"
    LOANS = "LOANS"
    CARDS = "CARDS"
    DEBTS = "DEBTS"


LIABILITIES = frozenset({NetWorthGroup.CARDS, NetWorthGroup.DEBTS})


@dataclass(frozen=True)
class NetWorthItem:
    """Un monto en su moneda de origen; los pasivos también van en positivo."""

    group: NetWorthGroup
    currency: Currency
    amount: Decimal


class NetWorthSource(Protocol):
    """Lo implementa cada módulo con lo que tiene o debe el usuario hoy."""

    async def __call__(self) -> list[NetWorthItem]: ...
