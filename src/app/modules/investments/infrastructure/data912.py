"""Adaptador de data912: precios de BYMA y de EE.UU. (API pública, sin credenciales)."""

import json
from decimal import Decimal

import httpx2

from app.modules.investments.domain.instrument import Market
from app.shared.domain.money import Currency

# Acciones, CEDEARs, bonos, letras y ONs de BYMA: precio por unidad o cada 100 VN.
BYMA_PANELS = ("arg_stocks", "arg_cedears", "arg_bonds", "arg_notes", "arg_corp")
# data912 no distingue la bolsa de EE.UU.: el mismo precio vale para NYSE y NASDAQ.
USA_PANELS = ("usa_stocks", "usa_adrs")


def byma_currency(symbol: str, symbols: set[str]) -> Currency:
    """En BYMA el mismo título cotiza en pesos (GD30) y en dólares MEP o cable (GD30D, GD30C).
    Un ticker que termina en D o C sin su versión en pesos (AMD) es de pesos; si se equivoca, el
    precio no se guarda porque no coincide con la moneda del instrumento."""
    if symbol[-1] in "DC" and symbol[:-1] in symbols:
        return Currency.USD
    return Currency.ARS


class Data912Provider:
    def __init__(self, client: httpx2.AsyncClient, url: str) -> None:
        self.client = client
        self.url = url

    async def _panel(self, name: str) -> dict[str, Decimal]:
        response = await self.client.get(f"{self.url}/live/{name}", timeout=20)
        response.raise_for_status()
        rows = json.loads(response.content, parse_float=Decimal, parse_int=Decimal)
        # Sin operaciones el último precio viene en 0 o vacío: no es un precio.
        return {row["symbol"]: Decimal(row["c"]) for row in rows if row.get("c")}

    async def market_prices(self) -> dict[tuple[Market, str], dict[Currency, Decimal]]:
        quotes: dict[tuple[Market, str], dict[Currency, Decimal]] = {}
        for panel in BYMA_PANELS:
            prices = await self._panel(panel)
            for symbol, price in prices.items():
                quotes[(Market.BYMA, symbol)] = {byma_currency(symbol, set(prices)): price}
        for panel in USA_PANELS:
            for symbol, price in (await self._panel(panel)).items():
                for market in (Market.NYSE, Market.NASDAQ):
                    quotes[(market, symbol)] = {Currency.USD: price}
        return quotes
