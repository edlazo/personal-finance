"""Dobles en memoria para los casos de uso de cotizaciones."""

from types import TracebackType
from typing import Self

from app.modules.fx.domain.rate import ExchangeRate


class InMemoryRates:
    def __init__(self) -> None:
        self.items: list[ExchangeRate] = []

    async def add(self, rate: ExchangeRate) -> None:
        self.items.append(rate)


class FakeFxUnitOfWork:
    def __init__(self) -> None:
        self.rates = InMemoryRates()
        self.commits = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass
