"""Endpoints de reportes: patrimonio neto (US-047)."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Query, status
from pydantic import BaseModel

from app.modules.reports.application.net_worth import GetNetWorth
from app.shared.api.auth import CurrentUserId
from app.shared.api.contracts import Converter, NetWorthSources, Preference
from app.shared.domain.money import Currency
from app.shared.domain.net_worth import LIABILITIES, NetWorthGroup
from app.shared.domain.rates import RateType


class GroupResponse(BaseModel):
    group: NetWorthGroup
    liability: bool
    # Subtotal en cada moneda de origen.
    by_currency: dict[Currency, Decimal]
    # Convertido a cada moneda pedida.
    total: dict[Currency, Decimal]


class NetWorthResponse(BaseModel):
    rate_type: RateType
    net_worth: dict[Currency, Decimal]
    assets: dict[Currency, Decimal]
    liabilities: dict[Currency, Decimal]
    groups: list[GroupResponse]


router = APIRouter(
    prefix="/reports",
    tags=["reportes"],
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Token inválido o vencido"}},
)


@router.get(
    "/net-worth",
    summary="Mi patrimonio neto de hoy",
    description=(
        "Activos (cuentas, inversiones y préstamos otorgados) menos pasivos (tarjetas y deudas), "
        "por grupo y por moneda de origen. Sin `currency`, los totales vienen en ARS y en USD."
    ),
)
async def net_worth(
    user_id: CurrentUserId,
    sources: NetWorthSources,
    converter: Converter,
    preference: Preference,
    currency: Annotated[Currency | None, Query(description="Sin valor: ARS y USD")] = None,
    rate_type: Annotated[RateType | None, Query(description="Sin valor: mi preferida")] = None,
) -> NetWorthResponse:
    currencies = [currency] if currency else list(Currency)
    report = await GetNetWorth(sources, converter, preference)(
        user_id, currencies, rate_type=rate_type
    )
    return NetWorthResponse(
        rate_type=report.rate_type,
        net_worth=report.net_worth,
        assets=report.assets,
        liabilities=report.liabilities,
        groups=[
            GroupResponse(
                group=g.group,
                liability=g.group in LIABILITIES,
                by_currency=g.by_currency,
                total=g.total,
            )
            for g in report.groups
        ],
    )
