"""Endpoints de las tarjetas de crédito."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.cards.application.manage_cards import (
    CreateCard,
    GetCard,
    ListCards,
    PendingInstallments,
    RegisterPurchase,
)
from app.modules.cards.domain.card import CardNetwork, CreditCard
from app.modules.cards.domain.purchase import MAX_INSTALLMENTS, CardPurchase
from app.modules.cards.infrastructure.persistence import SqlAlchemyCardsUnitOfWork
from app.shared.api.auth import CurrentUserId
from app.shared.api.dependencies import get_session_factory
from app.shared.domain.money import Currency

Day = Annotated[int, Field(ge=1, le=31)]


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


def get_cards_uow(
    user_id: CurrentUserId,
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> SqlAlchemyCardsUnitOfWork:
    return SqlAlchemyCardsUnitOfWork(session_factory, user_id)


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
    description="Las de resúmenes que todavía no vencieron, por fecha de vencimiento.",
    responses={status.HTTP_404_NOT_FOUND: {"description": "La tarjeta no existe"}},
)
async def pending_installments(
    card_id: UUID, request: Request, uow: CardsUow
) -> list[InstallmentResponse]:
    today = datetime.now(ZoneInfo(request.app.state.settings.fx_timezone)).date()
    pending = await PendingInstallments(uow=uow)(card_id, today)
    return [InstallmentResponse.model_validate(i) for i in pending]
