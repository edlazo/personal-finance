"""Adaptador de dolarapi.com: cotizaciones del dólar en Argentina."""

import json
from datetime import datetime
from decimal import Decimal

import httpx2
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.modules.fx.domain.rate import PRECISION, ExchangeRate, RateSource
from app.shared.domain.rates import RateType

# "casa" de dolarapi -> tipo propio; el resto (mayorista, tarjeta) no se guarda.
CASAS = {
    "oficial": RateType.OFICIAL,
    "blue": RateType.BLUE,
    "bolsa": RateType.MEP,
    "contadoconliqui": RateType.CCL,
    "cripto": RateType.CRIPTO,
}


class DolarApiProvider:
    def __init__(self, client: httpx2.AsyncClient, url: str, *, retry_wait: float = 2) -> None:
        self.client = client
        self.url = url
        self.retry_wait = retry_wait

    async def fetch(self) -> list[ExchangeRate]:
        retrying = AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=self.retry_wait),
            retry=retry_if_exception_type(httpx2.HTTPError),
            reraise=True,
        )
        async for attempt in retrying:
            with attempt:
                response = await self.client.get(self.url, timeout=10)
                response.raise_for_status()
        # Los montos llegan como números JSON: se leen como Decimal, nunca como float.
        items = json.loads(response.content, parse_float=Decimal, parse_int=Decimal)
        return [
            ExchangeRate(
                CASAS[item["casa"]],
                Decimal(item["compra"]).quantize(PRECISION),
                Decimal(item["venta"]).quantize(PRECISION),
                datetime.fromisoformat(item["fechaActualizacion"]),
                RateSource.API,
            )
            for item in items
            if item.get("casa") in CASAS and item.get("compra") and item.get("venta")
        ]
