"""Deudas y préstamos con su cronograma de cuotas mensuales."""

from calendar import monthrange
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from app.shared.domain.errors import DomainError
from app.shared.domain.money import Currency

CENTS = Decimal("0.01")
MAX_INSTALLMENTS = 360


class DebtDirection(StrEnum):
    # Decisión del PO: una sola entidad; lo que me deben cuenta como activo.
    OWED = "OWED"
    LENT = "LENT"


class InvalidDebtError(DomainError):
    pass


def add_months(start: date, months: int) -> date:
    """El mismo día N meses después o, si el mes es más corto, su último día."""
    year, index = divmod(start.year * 12 + start.month - 1 + months, 12)
    return date(year, index + 1, min(start.day, monthrange(year, index + 1)[1]))


def _cents(value: Decimal, rounding: str = ROUND_HALF_UP) -> Decimal:
    return value.quantize(CENTS, rounding)


@dataclass(frozen=True)
class DebtInstallment:
    number: int
    due_date: date
    amount: Decimal
    principal: Decimal
    interest: Decimal


@dataclass
class Debt:
    user_id: UUID
    counterparty: str
    direction: DebtDirection
    currency: Currency
    principal: Decimal
    installments: int
    start_date: date
    # Tasa nominal anual en %, como la informa el banco (decisión del PO): sistema francés.
    annual_rate: Decimal | None = None
    # O una cuota fija cargada a mano, sin tasa.
    fixed_installment: Decimal | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.counterparty = self.counterparty.strip()
        if not self.counterparty:
            raise InvalidDebtError("El acreedor o deudor es obligatorio")
        if self.principal <= 0 or self.principal != _cents(self.principal):
            raise InvalidDebtError("El capital tiene que ser mayor a cero y con hasta 2 decimales")
        if not 1 <= self.installments <= MAX_INSTALLMENTS:
            raise InvalidDebtError(f"Las cuotas van de 1 a {MAX_INSTALLMENTS}")
        if self.annual_rate is not None and self.fixed_installment is not None:
            raise InvalidDebtError("Se carga la tasa o la cuota fija, no las dos")
        if self.annual_rate is not None and self.annual_rate < 0:
            raise InvalidDebtError("La tasa no puede ser negativa")
        fixed = self.fixed_installment
        if fixed is not None and (fixed <= 0 or fixed != _cents(fixed)):
            raise InvalidDebtError("La cuota tiene que ser mayor a cero y con hasta 2 decimales")
        if fixed is not None and fixed * self.installments < self.principal:
            raise InvalidDebtError("Las cuotas no alcanzan a cubrir el capital")
        if self.principal / self.installments < CENTS:
            raise InvalidDebtError("El capital no alcanza para esa cantidad de cuotas")
        # Mismo formato que devuelve la base: 2 decimales en montos y 4 en la tasa.
        self.principal = _cents(self.principal)
        if fixed is not None:
            self.fixed_installment = _cents(fixed)
        if self.annual_rate is not None:
            self.annual_rate = self.annual_rate.quantize(Decimal("0.0001"))

    def schedule(self) -> list[DebtInstallment]:
        """Cuotas mensuales desde un mes después del inicio (decisión del PO)."""
        n, rate = self.installments, (self.annual_rate or Decimal(0)) / 1200
        if rate:
            # Sistema francés: cuota constante; el interés se calcula sobre el saldo.
            payment = _cents(self.principal * rate / (1 - (1 + rate) ** -n))
        rest = _cents(self.principal / n, ROUND_DOWN)
        balance, schedule = self.principal, []
        for number in range(1, n + 1):
            interest = _cents(balance * rate)
            if rate:
                principal = balance if number == n else payment - interest
            else:
                # Sin tasa, el capital va en partes iguales y los centavos que sobran en la 1.
                principal = self.principal - rest * (n - 1) if number == 1 else rest
            amount = self.fixed_installment or principal + interest
            if self.fixed_installment is not None:
                interest = amount - principal
            balance -= principal
            schedule.append(
                DebtInstallment(
                    number, add_months(self.start_date, number), amount, principal, interest
                )
            )
        return schedule


class DebtRepository(Protocol):
    async def add(self, debt: Debt, installments: list[DebtInstallment]) -> None: ...

    async def list_debts(self) -> list[Debt]: ...

    async def get_debt(self, debt_id: UUID) -> Debt: ...

    async def installments(self, debt_id: UUID) -> list[DebtInstallment]: ...
