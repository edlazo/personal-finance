"""Endpoints de deudas y préstamos."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.debts.application.manage_debts import (
    CreateDebt,
    GetDebt,
    ListDebts,
    RegisterDebtPayment,
)
from app.modules.debts.domain.debt import MAX_INSTALLMENTS, Debt, DebtDirection, DebtInstallment
from app.modules.debts.domain.payment import DebtBalance, DebtPayment
from app.modules.debts.infrastructure.persistence import SqlAlchemyDebtsUnitOfWork
from app.shared.api.auth import CurrentUserId
from app.shared.api.dependencies import get_session_factory
from app.shared.domain.money import Currency


class CreateDebtRequest(BaseModel):
    counterparty: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    # OWED: la debo; LENT: me la deben (cuenta como activo).
    direction: DebtDirection = DebtDirection.OWED
    currency: Currency
    principal: Decimal = Field(gt=0, max_digits=20, decimal_places=2)
    installments: int = Field(ge=1, le=MAX_INSTALLMENTS)
    start_date: date
    # TNA en %: sistema francés. O una cuota fija; sin ninguna, el capital en partes iguales.
    annual_rate: Decimal | None = Field(default=None, ge=0, max_digits=9, decimal_places=4)
    fixed_installment: Decimal | None = Field(default=None, gt=0, max_digits=20, decimal_places=2)


class InstallmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    number: int
    due_date: date
    amount: Decimal
    principal: Decimal
    interest: Decimal


class ScheduledInstallmentResponse(InstallmentResponse):
    # Cubierta entera por los pagos, aplicados a las cuotas en orden.
    paid: bool


class DebtResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    counterparty: str
    direction: DebtDirection
    currency: Currency
    principal: Decimal
    installments: int
    start_date: date
    annual_rate: Decimal | None
    fixed_installment: Decimal | None
    created_at: datetime
    paid: Decimal
    # Lo que falta pagar, con el interés de las cuotas que quedan.
    pending: Decimal
    next_installment: InstallmentResponse | None


class DebtDetailResponse(DebtResponse):
    schedule: list[ScheduledInstallmentResponse]


class RegisterPaymentRequest(BaseModel):
    account_id: UUID
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=2)
    date: date


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    debt_id: UUID
    account_id: UUID
    amount: Decimal
    date: date


def get_debts_uow(
    request: Request,
    user_id: CurrentUserId,
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> SqlAlchemyDebtsUnitOfWork:
    # app.state.cash_movements: implementación de ledger que conecta main.py (contrato de shared).
    return SqlAlchemyDebtsUnitOfWork(session_factory, user_id, request.app.state.cash_movements)


DebtsUow = Annotated[SqlAlchemyDebtsUnitOfWork, Depends(get_debts_uow)]

router = APIRouter(
    prefix="/debts",
    tags=["deudas"],
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Token inválido o vencido"}},
)


def _summary(debt: Debt, balance: DebtBalance) -> DebtResponse:
    return DebtResponse.model_validate(vars(debt) | vars(balance), from_attributes=True)


def _detail(
    debt: Debt, schedule: list[DebtInstallment], balance: DebtBalance
) -> DebtDetailResponse:
    return DebtDetailResponse(
        **_summary(debt, balance).model_dump(),
        schedule=[
            ScheduledInstallmentResponse(**vars(i), paid=i.number <= balance.paid_installments)
            for i in schedule
        ],
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una deuda o un préstamo",
    description=(
        "Genera las cuotas mensuales desde un mes después del inicio: sistema francés con la TNA, "
        "cuota fija o, sin ninguna, el capital en partes iguales. No mueve plata."
    ),
)
async def create_debt(
    body: CreateDebtRequest, user_id: CurrentUserId, uow: DebtsUow
) -> DebtDetailResponse:
    debt = Debt(
        user_id,
        body.counterparty,
        body.direction,
        body.currency,
        body.principal,
        body.installments,
        body.start_date,
        body.annual_rate,
        body.fixed_installment,
    )
    schedule = await CreateDebt(uow=uow)(debt)
    return _detail(debt, schedule, DebtBalance.of(schedule, Decimal("0.00")))


@router.get(
    "",
    summary="Mis deudas y préstamos",
    description="Por fecha de inicio, con lo pagado, lo que falta pagar y la próxima cuota.",
)
async def list_debts(uow: DebtsUow) -> list[DebtResponse]:
    return [_summary(debt, balance) for debt, balance in await ListDebts(uow=uow)()]


@router.get(
    "/{debt_id}",
    summary="Ver una deuda con su cronograma",
    responses={status.HTTP_404_NOT_FOUND: {"description": "La deuda no existe"}},
)
async def get_debt(debt_id: UUID, uow: DebtsUow) -> DebtDetailResponse:
    return _detail(*await GetDebt(uow=uow)(debt_id))


@router.post(
    "/{debt_id}/payments",
    status_code=status.HTTP_201_CREATED,
    summary="Pagar una deuda o cobrar un préstamo",
    description=(
        "Monto libre que se aplica a las cuotas en orden. Sale (o entra, si es un préstamo) de "
        "una cuenta activa en la moneda de la deuda, como un movimiento sin categoría. No puede "
        "superar lo que falta pagar."
    ),
    responses={status.HTTP_404_NOT_FOUND: {"description": "La deuda o la cuenta no existe"}},
)
async def register_payment(
    debt_id: UUID, body: RegisterPaymentRequest, user_id: CurrentUserId, uow: DebtsUow
) -> PaymentResponse:
    payment = DebtPayment(user_id, debt_id, body.account_id, body.amount, body.date)
    return PaymentResponse.model_validate(await RegisterDebtPayment(uow=uow)(payment))
