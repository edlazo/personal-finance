"""Adaptador de CoinGecko: precio de las cripto por símbolo, en USD y ARS."""

import json
from decimal import Decimal

import httpx2
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.shared.domain.money import Currency

CURRENCIES = {"usd": Currency.USD, "ars": Currency.ARS}


class CoinGeckoProvider:
    def __init__(
        self,
        client: httpx2.AsyncClient,
        url: str,
        *,
        api_key: str | None = None,
        retry_wait: float = 2,
    ) -> None:
        self.client = client
        self.url = url
        self.api_key = api_key
        self.retry_wait = retry_wait

    async def prices(self, tickers: set[str]) -> dict[str, dict[Currency, Decimal]]:
        # shortcut: CoinGecko acepta hasta 50 símbolos por pedido; partir si algún día hay más.
        params = {
            "symbols": ",".join(sorted(t.lower() for t in tickers)),
            "vs_currencies": ",".join(CURRENCIES),
            # Ante símbolos repetidos elige la moneda de mayor capitalización.
            "include_tokens": "top",
        }
        headers = {"x-cg-demo-api-key": self.api_key} if self.api_key else {}
        retrying = AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=self.retry_wait),
            retry=retry_if_exception_type(httpx2.HTTPError),
            reraise=True,
        )
        async for attempt in retrying:
            with attempt:
                response = await self.client.get(
                    f"{self.url}/simple/price", params=params, headers=headers, timeout=10
                )
                response.raise_for_status()
        body = json.loads(response.content, parse_float=Decimal, parse_int=Decimal)
        return {
            symbol.upper(): {
                CURRENCIES[key]: Decimal(value)
                for key, value in quotes.items()
                if key in CURRENCIES
            }
            for symbol, quotes in body.items()
        }
