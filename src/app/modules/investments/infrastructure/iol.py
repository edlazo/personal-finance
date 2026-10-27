"""Adaptador de IOL: el portafolio de la cuenta, de solo lectura."""

import json
from decimal import Decimal

import httpx2
import structlog

from app.modules.investments.domain.instrument import InstrumentType, Market
from app.modules.investments.domain.portfolio import BrokerHolding
from app.shared.domain.money import Currency

logger = structlog.get_logger()

# Lo que no está acá (fondos, cauciones, opciones) se saltea y queda en el log.
TYPES = {
    "acciones": InstrumentType.STOCK,
    "cedears": InstrumentType.CEDEAR,
    "titulospublicos": InstrumentType.BOND,
    "letras": InstrumentType.BOND,
    "obligacionesnegociables": InstrumentType.ON,
}
MARKETS = {"bcba": Market.BYMA, "nyse": Market.NYSE, "nasdaq": Market.NASDAQ}
CURRENCIES = {"peso_argentino": Currency.ARS, "dolar_estadounidense": Currency.USD}


class IolClient:
    def __init__(self, client: httpx2.AsyncClient, url: str) -> None:
        self.client = client
        self.url = url

    async def portfolio(self, username: str, password: str) -> list[BrokerHolding]:
        # Sin reintentos: cada intento gasta cupo de IOL. El refresh token vence antes de la
        # próxima corrida, así que cada una pide tokens con usuario y contraseña (spike PF-48).
        login = {"grant_type": "password", "username": username, "password": password}
        token = await self.client.post(f"{self.url}/token", data=login, timeout=20)
        token.raise_for_status()
        response = await self.client.get(
            f"{self.url}/api/v2/portafolio/argentina",
            headers={"Authorization": f"Bearer {token.json()['access_token']}"},
            timeout=20,
        )
        response.raise_for_status()
        body = json.loads(response.content, parse_float=Decimal, parse_int=Decimal)
        holdings = []
        for asset in body.get("activos", []):
            title = asset["titulo"]
            kind = TYPES.get(str(title["tipo"]).lower())
            market = MARKETS.get(str(title["mercado"]).lower())
            currency = CURRENCIES.get(str(title["moneda"]).lower())
            if kind is None or market is None or currency is None:
                logger.warning(
                    "iol_holding_skipped",
                    ticker=title["simbolo"],
                    type=title["tipo"],
                    market=title["mercado"],
                    currency=title["moneda"],
                )
                continue
            holdings.append(
                BrokerHolding(
                    title["simbolo"],
                    title["descripcion"],
                    kind,
                    market,
                    currency,
                    Decimal(asset["cantidad"]),
                    Decimal(asset["ppc"]),
                    Decimal(asset["ultimoPrecio"]),
                )
            )
        return holdings
