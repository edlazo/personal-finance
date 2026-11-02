"""Endpoints de las tarjetas de crédito."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Request, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.cards.application.manage_cards import (
    CreateCard,
    GetCard,
    GetStatement,
    ListCards,
    PendingInstallments,
    RegisterPayment,
    RegisterPurchase,
)
from app.modules.cards.domain.card import CardNetwork, CreditCard
from app.modules.cards.domain.purchase import MAX_INSTALLMENTS, CardPurchase
from app.modules.cards.infrastructure.persistence import SqlAlchemyCardsUnitOfWork
from app.shared.api.auth import CurrentUserId
from app.shared.api.dependencies import get_session_factory
from app.shared.domain.money import Currency

Day = Annotated[int, Field(ge=1, le=31)]
# El mes de cierre del resumen.
Period = Annotated[str, Path(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", examples=["2026-11"])]


class CreateCardRequest(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    network: CardNetwork
    closing_day: Day
    due_day: Day
    dual_currency: bool = False
    limit: Decimal | None = Field(default=None, gt=0, max_digits=20, decimal_places=2)


class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    network: CardNetwork
    closing_day: int
    due_day: int
    dual_currency: bool
    # Siempre ARS; también USD si es bimonetaria.
    currencies: list[Currency]
    limit: Decimal | None
    created_at: datetime


class RegisterPurchaseRequest(BaseModel):
    description: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
    ]
    # El total de la compra; se reparte entre las cuotas.
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=2)
    currency: Currency = Currency.ARS
    installments: int = Field(default=1, ge=1, le=MAX_INSTALLMENTS)
    date: date


class InstallmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    purchase_id: UUID
    description: str
    number: int
    count: int
    amount: Decimal
    currency: Currency
    # Cierre y vencimiento del resumen en el que entra la cuota.
    closing_date: date
    due_date: date
    purchase_date: date


class StatementResponse(BaseModel):
    period: str
    closing_date: date
    due_date: date
    items: list[InstallmentResponse]
    total_ars: Decimal
    total_usd: Decimal
    paid_ars: Decimal
    paid_usd: Decimal
    # Lo que falta pagar: un pago parcial deja saldo.
    pending_ars: Decimal
    pending_usd: Decimal


class RegisterPaymentRequest(BaseModel):
    account_id: UUID
    amount: Decimal = Field(gt=0, max_digits=20, decimal_places=2)
    currency: Currency = Currency.ARS
    date: date


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    closing_date: date
    amount: Decimal
    currency: Currency
    date: date


def get_cards_uow(
    request: Request,
    user_id: CurrentUserId,
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> SqlAlchemyCardsUnitOfWork:
    # app.state.cash_movements: implementación de ledger que conecta main.py (contrato de shared).
    return SqlAlchemyCardsUnitOfWork(session_factory, user_id, request.app.state.cash_movements)


CardsUow = Annotated[SqlAlchemyCardsUnitOfWork, Depends(get_cards_uow)]

router = APIRouter(
    prefix="/credit-cards",
    tags=["tarjetas"],
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Token inválido o vencido"}},
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta una tarjeta de crédito",
    description=(
        "Cierre y vencimiento son días del mes; en un mes más corto se usa su último día. "
        "El límite es en pesos y es opcional."
    ),
)
async def create_card(
    body: CreateCardRequest, user_id: CurrentUserId, uow: CardsUow
) -> CardResponse:
    card = CreditCard(
        user_id,
        body.name,
        body.network,
        body.closing_day,
        body.due_day,
        body.dual_currency,
        body.limit,
    )
    return CardResponse.model_validate(await CreateCard(uow=uow)(card))


@router.get("", summary="Mis tarjetas de crédito", description="Ordenadas por nombre.")
async def list_cards(uow: CardsUow) -> list[CardResponse]:
    return [CardResponse.model_validate(c) for c in await ListCards(uow=uow)()]


@router.get(
    "/{card_id}",
    summary="Ver una tarjeta de crédito",
    responses={status.HTTP_404_NOT_FOUND: {"description": "La tarjeta no existe"}},
)
async def get_card(card_id: UUID, uow: CardsUow) -> CardResponse:
    return CardResponse.model_validate(await GetCard(uow=uow)(card_id))


@router.post(
    "/{card_id}/purchases",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una compra, en una o más cuotas",
    description=(
        "Devuelve sus cuotas: una por resumen desde el que incluye la fecha de compra. Los "
        "centavos que sobran van en la primera. En dólares, solo con tarjetas bimonetarias."
    ),
    responses={status.HTTP_404_NOT_FOUND: {"description": "La tarjeta no existe"}},
)
async def register_purchase(
    card_id: UUID, body: RegisterPurchaseRequest, user_id: CurrentUserId, uow: CardsUow
) -> list[InstallmentResponse]:
    purchase = CardPurchase(
        user_id, card_id, body.description, body.amount, body.currency, body.installments, body.date
    )
    return [
        InstallmentResponse.model_validate(i) for i in await RegisterPurchase(uow=uow)(purchase)
    ]


@router.get(
    "/{card_id}/installments",
    summary="Cuotas pendientes de una tarjeta",
    description="Las de resúmenes sin pagar completos en su moneda, por vencimiento.",
    responses={status.HTTP_404_NOT_FOUND: {"description": "La tarjeta no existe"}},
)
async def pending_installments(card_id: UUID, uow: CardsUow) -> list[InstallmentResponse]:
    pending = await PendingInstallments(uow=uow)(card_id)
    return [InstallmentResponse.model_validate(i) for i in pending]


@router.get(
    "/{card_id}/statements/{period}",
    summary="Resumen de un período",
    description=(
        "El período es el mes de cierre (AAAA-MM): consumos y cuotas que entran en ese resumen, "
        "con los totales en pesos y en dólares, el cierre y el vencimiento."
    ),
    responses={status.HTTP_404_NOT_FOUND: {"description": "La tarjeta no existe"}},
)
async def get_statement(
    card_id: UUID,
    period: Period,
    uow: CardsUow,
) -> StatementResponse:
    statement = await GetStatement(uow=uow)(card_id, *_year_month(period))
    return StatementResponse(
        period=period,
        closing_date=statement.closing_date,
        due_date=statement.due_date,
        items=[InstallmentResponse.model_validate(i) for i in statement.items],
        total_ars=statement.total(Currency.ARS),
        total_usd=statement.total(Currency.USD),
        paid_ars=statement.paid.get(Currency.ARS, Decimal("0.00")),
        paid_usd=statement.paid.get(Currency.USD, Decimal("0.00")),
        pending_ars=statement.pending(Currency.ARS),
        pending_usd=statement.pending(Currency.USD),
    )


def _year_month(period: str) -> tuple[int, int]:
    year, month = period.split("-")
    return int(year), int(month)


@router.post(
    "/{card_id}/statements/{period}/payments",
    status_code=status.HTTP_201_CREATED,
    summary="Pagar un resumen, total o parcial",
    description=(
        "Sale de una cuenta activa en la moneda que se paga, como un movimiento sin categoría "
        "(no es un gasto). No puede superar lo que falta pagar del resumen en esa moneda."
    ),
    responses={status.HTTP_404_NOT_FOUND: {"description": "La tarjeta o la cuenta no existe"}},
)
async def register_payment(
    card_id: UUID,
    period: Period,
    body: RegisterPaymentRequest,
    user_id: CurrentUserId,
    uow: CardsUow,
) -> PaymentResponse:
    payment = await RegisterPayment(uow=uow)(
        user_id,
        card_id,
        *_year_month(period),
        account_id=body.account_id,
        amount=body.amount,
        currency=body.currency,
        on=body.date,
    )
    return PaymentResponse.model_validate(payment)
