"""Endpoints del catálogo de instrumentos."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.investments.application.manage_instruments import (
    CreateInstrument,
    ListInstruments,
)
from app.modules.investments.domain.instrument import InstrumentType, Market
from app.modules.investments.infrastructure.persistence import SqlAlchemyInvestmentsUnitOfWork
from app.shared.api.auth import CurrentUserId
from app.shared.api.dependencies import get_session_factory
from app.shared.domain.money import Currency


class CreateInstrumentRequest(BaseModel):
    ticker: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    type: InstrumentType
    market: Market
    currency: Currency


class InstrumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticker: str
    name: str
    type: InstrumentType
    market: Market
    currency: Currency
    # 100 para bonos y ONs (cotizan cada 100 VN); 1 para el resto.
    quote_unit: int
    created_at: datetime


def get_investments_uow(
    user_id: CurrentUserId,
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> SqlAlchemyInvestmentsUnitOfWork:
    return SqlAlchemyInvestmentsUnitOfWork(session_factory, user_id)


InvestmentsUow = Annotated[SqlAlchemyInvestmentsUnitOfWork, Depends(get_investments_uow)]

router = APIRouter(
    prefix="/instruments",
    tags=["inversiones"],
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Token inválido o vencido"}},
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Agregar un instrumento a mi catálogo",
    description="El ticker se guarda en mayúsculas y es único por mercado.",
    responses={status.HTTP_409_CONFLICT: {"description": "Ticker repetido en ese mercado"}},
)
async def create_instrument(
    body: CreateInstrumentRequest, user_id: CurrentUserId, uow: InvestmentsUow
) -> InstrumentResponse:
    instrument = await CreateInstrument(uow=uow)(
        user_id,
        ticker=body.ticker,
        name=body.name,
        instrument_type=body.type,
        market=body.market,
        currency=body.currency,
    )
    return InstrumentResponse.model_validate(instrument)


@router.get("", summary="Mi catálogo de instrumentos", description="Ordenado por mercado y ticker.")
async def list_instruments(uow: InvestmentsUow) -> list[InstrumentResponse]:
    return [InstrumentResponse.model_validate(i) for i in await ListInstruments(uow=uow)()]
