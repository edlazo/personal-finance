"""Endpoints de las tarjetas de crédito."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.cards.application.manage_cards import CreateCard, GetCard, ListCards
from app.modules.cards.domain.card import CardNetwork, CreditCard
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
