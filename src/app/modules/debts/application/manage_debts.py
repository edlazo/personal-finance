"""Casos de uso: registrar, listar y ver deudas y préstamos."""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.modules.debts.domain.debt import Debt, DebtInstallment, DebtRepository
from app.shared.application.unit_of_work import UnitOfWork


class DebtsUnitOfWork(UnitOfWork, Protocol):
    @property
    def debts(self) -> DebtRepository: ...


@dataclass(frozen=True)
class CreateDebt:
    """Decisión del PO: registrarla no mueve plata; las cuotas sí, al pagarlas."""

    uow: DebtsUnitOfWork

    async def __call__(self, debt: Debt) -> list[DebtInstallment]:
        installments = debt.schedule()
        async with self.uow:
            await self.uow.debts.add(debt, installments)
            await self.uow.commit()
        return installments


@dataclass(frozen=True)
class ListDebts:
    uow: DebtsUnitOfWork

    async def __call__(self) -> list[Debt]:
        async with self.uow:
            return await self.uow.debts.list_debts()


@dataclass(frozen=True)
class GetDebt:
    uow: DebtsUnitOfWork

    async def __call__(self, debt_id: UUID) -> tuple[Debt, list[DebtInstallment]]:
        async with self.uow:
            debt = await self.uow.debts.get_debt(debt_id)
            return debt, await self.uow.debts.installments(debt_id)
