"""Casos de uso: crear y listar instrumentos."""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.modules.investments.domain.instrument import (
    Instrument,
    InstrumentRepository,
    InstrumentTickerTakenError,
    InstrumentType,
    Market,
)
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.money import Currency


class InvestmentsUnitOfWork(UnitOfWork, Protocol):
    @property
    def instruments(self) -> InstrumentRepository: ...


@dataclass(frozen=True)
class CreateInstrument:
    uow: InvestmentsUnitOfWork

    async def __call__(
        self,
        user_id: UUID,
        *,
        ticker: str,
        name: str,
        instrument_type: InstrumentType,
        market: Market,
        currency: Currency,
    ) -> Instrument:
        instrument = Instrument(user_id, ticker, name, instrument_type, market, currency)
        async with self.uow:
            if await self.uow.instruments.ticker_taken(instrument.ticker, market):
                raise InstrumentTickerTakenError
            await self.uow.instruments.add(instrument)
            await self.uow.commit()
        return instrument


@dataclass(frozen=True)
class ListInstruments:
    uow: InvestmentsUnitOfWork

    async def __call__(self) -> list[Instrument]:
        async with self.uow:
            return await self.uow.instruments.list_instruments()
