"""Casos de uso: registrar, listar, ver y pagar deudas y préstamos."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.modules.debts.domain.debt import Debt, DebtDirection, DebtInstallment, DebtRepository
from app.modules.debts.domain.payment import (
    DebtBalance,
    DebtPayment,
    InvalidPaymentError,
    PaymentRepository,
)
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.cash import CashMovements
from app.shared.domain.net_worth import NetWorthGroup, NetWorthItem

ZERO = Decimal("0.00")


class DebtsUnitOfWork(UnitOfWork, Protocol):
    @property
    def debts(self) -> DebtRepository: ...

    @property
    def payments(self) -> PaymentRepository: ...

    @property
    def cash(self) -> CashMovements: ...


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

    async def __call__(self) -> list[tuple[Debt, DebtBalance]]:
        async with self.uow:
            paid = await self.uow.payments.paid()
            # shortcut: una consulta de cuotas por deuda; agruparlas si alguien tiene cientos.
            return [
                (d, DebtBalance.of(await self.uow.debts.installments(d.id), paid.get(d.id, ZERO)))
                for d in await self.uow.debts.list_debts()
            ]


@dataclass(frozen=True)
class GetDebt:
    uow: DebtsUnitOfWork

    async def __call__(self, debt_id: UUID) -> tuple[Debt, list[DebtInstallment], DebtBalance]:
        async with self.uow:
            debt = await self.uow.debts.get_debt(debt_id)
            installments = await self.uow.debts.installments(debt_id)
            paid = (await self.uow.payments.paid()).get(debt_id, ZERO)
        return debt, installments, DebtBalance.of(installments, paid)


@dataclass(frozen=True)
class RegisterDebtPayment:
    """Pago de una deuda o cobro de un préstamo: sale o entra de una cuenta en su moneda."""

    uow: DebtsUnitOfWork

    async def __call__(self, payment: DebtPayment) -> DebtPayment:
        async with self.uow:
            debt = await self.uow.debts.get_debt(payment.debt_id)
            paid = (await self.uow.payments.paid()).get(debt.id, ZERO)
            pending = DebtBalance.of(await self.uow.debts.installments(debt.id), paid).pending
            if payment.amount > pending:
                raise InvalidPaymentError(f"Falta pagar {pending} {debt.currency}")
            account = await self.uow.cash.account(payment.account_id)
            if account.archived or account.currency is not debt.currency:
                raise InvalidPaymentError(f"Se paga desde una cuenta activa en {debt.currency}")
            await self.uow.payments.add(payment)
            # Decisión del PO: sin categoría, como el pago de la tarjeta; no es gasto ni ingreso.
            lent = debt.direction is DebtDirection.LENT
            await self.uow.cash.record_trade(
                payment.account_id,
                payment.amount,
                incoming=lent,
                on=payment.date,
                trade_id=payment.id,
                description=f"{'Cobro de' if lent else 'Pago a'} {debt.counterparty}",
            )
            await self.uow.commit()
        return payment


# Lo que me deben es activo; lo que debo, pasivo.
GROUPS = {DebtDirection.LENT: NetWorthGroup.LOANS, DebtDirection.OWED: NetWorthGroup.DEBTS}


@dataclass(frozen=True)
class DebtsNetWorth:
    """Fuente del patrimonio: lo que falta pagar de cada deuda o préstamo."""

    uow: DebtsUnitOfWork

    async def __call__(self) -> list[NetWorthItem]:
        return [
            NetWorthItem(GROUPS[debt.direction], debt.currency, balance.pending)
            for debt, balance in await ListDebts(uow=self.uow)()
        ]
