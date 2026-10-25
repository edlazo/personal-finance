"""Dobles en memoria para los casos de uso de inversiones."""

from types import TracebackType
from typing import Self

from app.modules.investments.domain.instrument import Instrument, Market


class InMemoryInstruments:
    def __init__(self) -> None:
        self.items: list[Instrument] = []

    async def ticker_taken(self, ticker: str, market: Market) -> bool:
        return any((i.ticker, i.market) == (ticker, market) for i in self.items)

    async def add(self, instrument: Instrument) -> None:
        self.items.append(instrument)

    async def list_instruments(self) -> list[Instrument]:
        return sorted(self.items, key=lambda i: (i.market, i.ticker))


class FakeInvestmentsUnitOfWork:
    def __init__(self) -> None:
        self.instruments = InMemoryInstruments()
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
