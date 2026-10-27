"""Contrato para que otros módulos muevan plata de una cuenta de ledger (US-027)."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.shared.domain.money import Currency


@dataclass(frozen=True)
class CashAccount:
    id: UUID
    currency: Currency
    # Comitente o wallet cripto: las únicas cuentas que operan instrumentos.
    holds_investments: bool
    archived: bool


class CashMovements(Protocol):
    """Lo implementa ledger dentro de la misma transacción de base de quien lo usa."""

    async def account(self, account_id: UUID) -> CashAccount:
        """La cuenta del usuario; NotFoundError si no existe o es de otro."""
        ...

    async def record_trade(
        self,
        account_id: UUID,
        amount: Decimal,
        *,
        incoming: bool,
        on: date,
        trade_id: UUID,
        description: str,
    ) -> None:
        """Movimiento sin categoría ligado a la operación; no cuenta como ingreso ni gasto."""
        ...

    async def record_income(
        self, account_id: UUID, amount: Decimal, *, on: date, trade_id: UUID, description: str
    ) -> None:
        """Ingreso en la categoría "Rentas" ligado al evento (dividendo o cupón)."""
        ...
