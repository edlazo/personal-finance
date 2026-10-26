from decimal import Decimal
from urllib.parse import parse_qs

import httpx2
import pytest
from structlog.testing import capture_logs

from app.modules.investments.domain.instrument import InstrumentType, Market
from app.modules.investments.domain.portfolio import BrokerHolding
from app.modules.investments.infrastructure.iol import IolClient
from app.shared.domain.money import Currency

PORTFOLIO = b"""{"pais": "argentina", "activos": [
  {"cantidad": 10, "ppc": 6000.5, "ultimoPrecio": 6500,
   "titulo": {"simbolo": "GGAL", "descripcion": "Grupo Galicia", "tipo": "ACCIONES",
              "mercado": "BCBA", "moneda": "peso_Argentino"}},
  {"cantidad": 1000, "ppc": 70000, "ultimoPrecio": 75000.25,
   "titulo": {"simbolo": "AL30D", "descripcion": "Bonar 2030", "tipo": "TitulosPublicos",
              "mercado": "BCBA", "moneda": "dolar_Estadounidense"}},
  {"cantidad": 3, "ppc": 1, "ultimoPrecio": 1,
   "titulo": {"simbolo": "FCI1", "descripcion": "Fondo", "tipo": "FondoComundeInversion",
              "mercado": "BCBA", "moneda": "peso_Argentino"}}
]}"""


async def test_two_calls_bring_the_portfolio_and_unknown_types_are_skipped() -> None:
    calls: list[httpx2.Request] = []

    def handle(request: httpx2.Request) -> httpx2.Response:
        calls.append(request)
        if request.url.path == "/token":
            return httpx2.Response(200, json={"access_token": "tok", "refresh_token": "r"})
        return httpx2.Response(200, content=PORTFOLIO)

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handle))
    with capture_logs() as logs:
        holdings = await IolClient(client, "https://iol.test").portfolio("elias", "clave")

    token, portfolio = calls
    assert parse_qs(token.content.decode()) == {
        "grant_type": ["password"],
        "username": ["elias"],
        "password": ["clave"],
    }
    assert portfolio.url.path == "/api/v2/portafolio/argentina"
    assert portfolio.headers["Authorization"] == "Bearer tok"
    ars, usd, stock, bond = Currency.ARS, Currency.USD, InstrumentType.STOCK, InstrumentType.BOND
    assert holdings == [
        BrokerHolding(
            "GGAL",
            "Grupo Galicia",
            stock,
            Market.BYMA,
            ars,
            Decimal("10"),
            Decimal("6000.5"),
            Decimal("6500"),
        ),
        BrokerHolding(
            "AL30D",
            "Bonar 2030",
            bond,
            Market.BYMA,
            usd,
            Decimal("1000"),
            Decimal("70000"),
            Decimal("75000.25"),
        ),
    ]
    assert [(log["event"], log["ticker"]) for log in logs] == [("iol_holding_skipped", "FCI1")]


async def test_wrong_credentials_stop_before_the_portfolio_call() -> None:
    calls: list[httpx2.Request] = []

    def handle(request: httpx2.Request) -> httpx2.Response:
        calls.append(request)
        return httpx2.Response(400, json={"error": "invalid_grant"})

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handle))
    with pytest.raises(httpx2.HTTPStatusError) as error:
        await IolClient(client, "https://iol.test").portfolio("elias", "mal")

    assert "mal" not in str(error.value)
    assert len(calls) == 1
