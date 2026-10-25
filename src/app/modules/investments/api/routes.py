"""Endpoints del catálogo de instrumentos."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.investments.application.manage_instruments import (
    CreateInstrument,
    ListInstruments,
)
from app.modules.investments.application.register_trade import RegisterTrade
from app.modules.investments.domain.instrument import InstrumentType, Market
from app.modules.investments.domain.trade import TradeSide
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


class CreateTradeRequest(BaseModel):
    account_id: UUID
    instrument_id: UUID
    side: TradeSide
    quantity: Decimal = Field(gt=0, max_digits=28, decimal_places=8)
    # Por unidad; en bonos y ONs, cada 100 de valor nominal.
    price: Decimal = Field(gt=0, max_digits=28, decimal_places=10)
    fee: Decimal = Field(default=Decimal("0"), ge=0, max_digits=20, decimal_places=2)
    date: date


class TradeResponse(BaseModel):
    id: UUID
    account_id: UUID
    instrument_id: UUID
    side: TradeSide
    quantity: Decimal
    price: Decimal
    fee: Decimal
    date: date
    # Lo que salió (compra) o entró (venta) de la cuenta.
    cash: Decimal


def get_investments_uow(
    request: Request,
    user_id: CurrentUserId,
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> SqlAlchemyInvestmentsUnitOfWork:
    # app.state.cash_movements: implementación de ledger que conecta main.py (contrato de shared).
    return SqlAlchemyInvestmentsUnitOfWork(
        session_factory, user_id, request.app.state.cash_movements
    )


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


trades_router = APIRouter(
    prefix="/trades",
    tags=["inversiones"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Token inválido o vencido"},
        status.HTTP_404_NOT_FOUND: {"description": "La cuenta o el instrumento no existe"},
    },
)


@trades_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una compra o venta",
    description=(
        "Desde una comitente o wallet de la moneda del instrumento. La compra debita precio x "
        "cantidad (/100 en bonos y ONs) más la comisión; la venta acredita lo mismo menos la "
        "comisión y no puede superar la tenencia de esa cuenta."
    ),
)
async def create_trade(
    body: CreateTradeRequest, user_id: CurrentUserId, uow: InvestmentsUow
) -> TradeResponse:
    trade, cash = await RegisterTrade(uow=uow)(
        user_id,
        account_id=body.account_id,
        instrument_id=body.instrument_id,
        side=body.side,
        quantity=body.quantity,
        price=body.price,
        fee=body.fee,
        on=body.date,
    )
    return TradeResponse(**vars(trade) | {"cash": cash})
