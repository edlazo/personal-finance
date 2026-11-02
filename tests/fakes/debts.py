from collections import defaultdict
from decimal import Decimal
from types import TracebackType
from typing import Self
from uuid import UUID

from app.modules.debts.domain.debt import Debt, DebtInstallment
from app.modules.debts.domain.payment import DebtPayment
from app.shared.domain.errors import NotFoundError
from fakes.investments import FakeCash


class InMemoryDebts:
    def __init__(self) -> None:
        self.items: dict[UUID, tuple[Debt, list[DebtInstallment]]] = {}

    async def add(self, debt: Debt, installments: list[DebtInstallment]) -> None:
        self.items[debt.id] = (debt, installments)

    async def list_debts(self) -> list[Debt]:
        return sorted((d for d, _ in self.items.values()), key=lambda d: d.start_date)

    async def get_debt(self, debt_id: UUID) -> Debt:
        if debt_id not in self.items:
            raise NotFoundError("El recurso no existe")
        return self.items[debt_id][0]

    async def installments(self, debt_id: UUID) -> list[DebtInstallment]:
        return list(self.items[debt_id][1])


class InMemoryDebtPayments:
    def __init__(self) -> None:
        self.items: list[DebtPayment] = []

    async def add(self, payment: DebtPayment) -> None:
        self.items.append(payment)

    async def paid(self) -> dict[UUID, Decimal]:
        totals: dict[UUID, Decimal] = defaultdict(Decimal)
        for payment in self.items:
            totals[payment.debt_id] += payment.amount
        return dict(totals)


class FakeDebtsUnitOfWork:
    def __init__(self) -> None:
        self.debts = InMemoryDebts()
        self.payments = InMemoryDebtPayments()
        self.cash = FakeCash()
        self.commits = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass
