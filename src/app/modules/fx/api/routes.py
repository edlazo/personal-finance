"""Endpoints de cotizaciones."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.fx.application.query_rates import LatestRates, RateHistory
from app.modules.fx.application.register_rate import RegisterManualRate
from app.modules.fx.domain.rate import RateSource
from app.modules.fx.infrastructure.persistence import SqlAlchemyFxUnitOfWork
from app.shared.api.auth import CurrentUserId
from app.shared.api.dependencies import get_session_factory
from app.shared.domain.rates import RateType

Price = Annotated[Decimal, Field(gt=0, max_digits=28, decimal_places=10)]


class CreateRateRequest(BaseModel):
    type: RateType
    buy: Price
    sell: Price
    quoted_at: AwareDatetime


class RateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: RateType
    # Pesos por dólar; en JSON van como string decimal.
    buy: Decimal
    sell: Decimal
    quoted_at: datetime
    source: RateSource


def get_fx_uow(
    user_id: CurrentUserId,
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> SqlAlchemyFxUnitOfWork:
    return SqlAlchemyFxUnitOfWork(session_factory, user_id)


FxUow = Annotated[SqlAlchemyFxUnitOfWork, Depends(get_fx_uow)]

router = APIRouter(
    prefix="/fx",
    tags=["cotizaciones"],
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Token inválido o vencido"}},
)


@router.post(
    "/rates",
    status_code=status.HTTP_201_CREATED,
    summary="Cargar una cotización a mano",
    description="Solo la ve quien la carga. Nunca pisa valores anteriores: suma al historial.",
)
async def create_rate(body: CreateRateRequest, user_id: CurrentUserId, uow: FxUow) -> RateResponse:
    rate = await RegisterManualRate(uow=uow)(
        user_id, rate_type=body.type, buy=body.buy, sell=body.sell, quoted_at=body.quoted_at
    )
    return RateResponse.model_validate(rate)


@router.get(
    "/rates/latest",
    summary="Cotizaciones actuales",
    description="La más reciente de cada tipo, entre las de la API y las que cargué a mano.",
)
async def latest_rates(uow: FxUow) -> list[RateResponse]:
    return [RateResponse.model_validate(rate) for rate in await LatestRates(uow=uow)()]


@router.get(
    "/rates",
    summary="Historial de cotizaciones",
    description="De la más reciente a la más vieja. `from` y `to` son fecha y hora con zona.",
)
async def rate_history(
    uow: FxUow,
    rate_type: Annotated[RateType | None, Query(alias="type")] = None,
    since: Annotated[AwareDatetime | None, Query(alias="from")] = None,
    until: Annotated[AwareDatetime | None, Query(alias="to")] = None,
) -> list[RateResponse]:
    rates = await RateHistory(uow=uow)(rate_type, since=since, until=until)
    return [RateResponse.model_validate(rate) for rate in rates]
