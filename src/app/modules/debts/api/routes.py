"""Endpoints de deudas y préstamos."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.debts.application.manage_debts import CreateDebt, GetDebt, ListDebts
from app.modules.debts.domain.debt import MAX_INSTALLMENTS, Debt, DebtDirection
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


class DebtDetailResponse(DebtResponse):
    schedule: list[InstallmentResponse]


def get_debts_uow(
    user_id: CurrentUserId,
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> SqlAlchemyDebtsUnitOfWork:
    return SqlAlchemyDebtsUnitOfWork(session_factory, user_id)


DebtsUow = Annotated[SqlAlchemyDebtsUnitOfWork, Depends(get_debts_uow)]

router = APIRouter(
    prefix="/debts",
    tags=["deudas"],
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Token inválido o vencido"}},
)


def _detail(debt: Debt, schedule: list[object]) -> DebtDetailResponse:
    base = DebtResponse.model_validate(debt).model_dump()
    return DebtDetailResponse(
        **base, schedule=[InstallmentResponse.model_validate(i) for i in schedule]
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
    return _detail(debt, list(await CreateDebt(uow=uow)(debt)))


@router.get("", summary="Mis deudas y préstamos", description="Por fecha de inicio.")
async def list_debts(uow: DebtsUow) -> list[DebtResponse]:
    return [DebtResponse.model_validate(d) for d in await ListDebts(uow=uow)()]


@router.get(
    "/{debt_id}",
    summary="Ver una deuda con su cronograma",
    responses={status.HTTP_404_NOT_FOUND: {"description": "La deuda no existe"}},
)
async def get_debt(debt_id: UUID, uow: DebtsUow) -> DebtDetailResponse:
    debt, schedule = await GetDebt(uow=uow)(debt_id)
    return _detail(debt, list(schedule))
