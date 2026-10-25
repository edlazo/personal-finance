from datetime import UTC, datetime
from decimal import Decimal

import httpx2
import pytest

from app.modules.fx.domain.rate import RateSource
from app.modules.fx.infrastructure.dolarapi import DolarApiProvider
from app.shared.domain.rates import RateType

URL = "https://dolarapi.test/v1/dolares"
# Recorte de la respuesta real de https://dolarapi.com/v1/dolares.
PAYLOAD = b"""[
  {"moneda": "USD", "casa": "oficial", "nombre": "Oficial", "compra": 1405,
   "venta": 1455.5, "fechaActualizacion": "2026-10-24T17:57:00.000Z"},
  {"moneda": "USD", "casa": "bolsa", "nombre": "Bolsa", "compra": 1480.1,
   "venta": 1490.12345678901, "fechaActualizacion": "2026-10-24T17:58:00.000Z"},
  {"moneda": "USD", "casa": "tarjeta", "nombre": "Tarjeta", "compra": null,
   "venta": 1891.5, "fechaActualizacion": "2026-10-24T17:57:00.000Z"},
  {"moneda": "USD", "casa": "mayorista", "nombre": "Mayorista", "compra": 1400,
   "venta": 1410, "fechaActualizacion": "2026-10-24T17:57:00.000Z"}
]"""


def provider(*responses: int) -> tuple[DolarApiProvider, list[httpx2.Request]]:
    """Responde con esos códigos en orden; el último se repite."""
    calls: list[httpx2.Request] = []

    def handle(request: httpx2.Request) -> httpx2.Response:
        calls.append(request)
        code = responses[min(len(calls), len(responses)) - 1]
        return httpx2.Response(code, content=PAYLOAD if code == 200 else b"")

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handle))
    return DolarApiProvider(client, URL, retry_wait=0), calls


async def test_maps_the_known_casas_as_decimal_api_rates() -> None:
    dolarapi, _ = provider(200)

    rates = await dolarapi.fetch()

    assert [(r.type, r.buy, r.sell, r.source) for r in rates] == [
        (RateType.OFICIAL, Decimal("1405"), Decimal("1455.5"), RateSource.API),
        (RateType.MEP, Decimal("1480.1"), Decimal("1490.1234567890"), RateSource.API),
    ]
    assert rates[0].quoted_at == datetime(2026, 10, 24, 17, 57, tzinfo=UTC)


async def test_retries_before_giving_up() -> None:
    recovers, calls = provider(503, 503, 200)
    assert len(await recovers.fetch()) == 2
    assert len(calls) == 3

    broken, calls = provider(503)
    with pytest.raises(httpx2.HTTPStatusError):
        await broken.fetch()
    assert len(calls) == 3
