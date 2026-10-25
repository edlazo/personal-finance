"""Dobles en memoria para los casos de uso de cotizaciones."""

from datetime import datetime
from types import TracebackType
from typing import Self

from app.modules.fx.domain.rate import ExchangeRate
from app.shared.domain.rates import RateType


class InMemoryRates:
    def __init__(self) -> None:
        self.items: list[ExchangeRate] = []

    async def add(self, rate: ExchangeRate) -> None:
        self.items.append(rate)

    async def latest(self) -> list[ExchangeRate]:
        newest: dict[RateType, ExchangeRate] = {}
        for rate in sorted(self.items, key=lambda r: r.quoted_at):
            newest[rate.type] = rate
        return list(newest.values())

    # shortcut: el historial solo se usa contra Postgres (tests de integración).

    async def history(
        self, rate_type: RateType | None, *, since: datetime | None, until: datetime | None
    ) -> list[ExchangeRate]:
        return list(self.items)


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
