"""Dobles en memoria para los casos de uso de inversiones."""

from datetime import date
from decimal import Decimal
from types import TracebackType
from typing import Self
from uuid import UUID

from app.modules.investments.domain.credentials import Broker, BrokerCredentials
from app.modules.investments.domain.event import InstrumentEvent
from app.modules.investments.domain.instrument import Instrument, InstrumentType, Market
from app.modules.investments.domain.price import InstrumentPrice
from app.modules.investments.domain.trade import Trade, TradeSide
from app.shared.domain.cash import CashAccount
from app.shared.domain.errors import NotFoundError


class InMemoryInstruments:
    def __init__(self) -> None:
        self.items: list[Instrument] = []

    async def ticker_taken(self, ticker: str, market: Market) -> bool:
        return any((i.ticker, i.market) == (ticker, market) for i in self.items)

    async def add(self, instrument: Instrument) -> None:
        self.items.append(instrument)

    async def list_instruments(self) -> list[Instrument]:
        return sorted(self.items, key=lambda i: (i.market, i.ticker))

    async def get_instrument(self, instrument_id: UUID) -> Instrument:
        for instrument in self.items:
            if instrument.id == instrument_id:
                return instrument
        raise NotFoundError("El recurso no existe")


class InMemoryTrades:
    def __init__(self) -> None:
        self.items: list[Trade] = []

    async def add(self, trade: Trade) -> None:
        self.items.append(trade)

    async def list_trades(self) -> list[Trade]:
        return list(self.items)

    async def holding(self, account_id: UUID, instrument_id: UUID) -> Decimal:
        return sum(
            (
                t.quantity if t.side is TradeSide.BUY else -t.quantity
                for t in self.items
                if (t.account_id, t.instrument_id) == (account_id, instrument_id)
            ),
            Decimal("0"),
        )


class InMemoryEvents:
    def __init__(self) -> None:
        self.items: list[InstrumentEvent] = []

    async def add(self, event: InstrumentEvent) -> None:
        self.items.append(event)

    async def list_events(self) -> list[InstrumentEvent]:
        return list(self.items)

    async def amortized(self, account_id: UUID, instrument_id: UUID) -> Decimal:
        # Solo las amortizaciones tienen valor nominal.
        key = (account_id, instrument_id)
        found = [e.nominal for e in self.items if (e.account_id, e.instrument_id) == key]
        return sum((n for n in found if n is not None), Decimal("0"))


class InMemoryPrices:
    def __init__(self) -> None:
        self.items: list[InstrumentPrice] = []

    async def add(self, price: InstrumentPrice) -> None:
        self.items.append(price)

    async def latest_prices(self) -> dict[UUID, InstrumentPrice]:
        latest: dict[UUID, InstrumentPrice] = {}
        for price in sorted(self.items, key=lambda p: (p.date, p.created_at)):
            latest[price.instrument_id] = price
        return latest


class InMemoryCryptoStore:
    def __init__(self) -> None:
        self.instruments: list[Instrument] = []
        self.prices: list[InstrumentPrice] = []

    async def list_crypto(self) -> list[Instrument]:
        return [i for i in self.instruments if i.type is InstrumentType.CRYPTO]

    async def add(self, price: InstrumentPrice) -> None:
        self.prices.append(price)


class FakeCash:
    """Las cuentas de ledger que ve investments y los movimientos que pidió."""

    def __init__(self) -> None:
        self.accounts: dict[UUID, CashAccount] = {}
        self.recorded: list[tuple[UUID, Decimal, bool]] = []
        self.incomes: list[tuple[UUID, Decimal]] = []

    async def account(self, account_id: UUID) -> CashAccount:
        if account_id not in self.accounts:
            raise NotFoundError("El recurso no existe")
        return self.accounts[account_id]

    async def record_trade(
        self,
        account_id: UUID,
        amount: Decimal,
        *,
        incoming: bool,
        on: date,
        trade_id: UUID,
        description: str,
    ) -> None:
        self.recorded.append((account_id, amount, incoming))

    async def record_income(
        self, account_id: UUID, amount: Decimal, *, on: date, trade_id: UUID, description: str
    ) -> None:
        self.incomes.append((account_id, amount))


class FakePriceSyncUnitOfWork:
    def __init__(self) -> None:
        self.store = InMemoryCryptoStore()
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


class FakeInvestmentsUnitOfWork:
    def __init__(self) -> None:
        self.instruments = InMemoryInstruments()
        self.trades = InMemoryTrades()
        self.prices = InMemoryPrices()
        self.events = InMemoryEvents()
        self.cash = FakeCash()
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


class InMemoryCredentials:
    def __init__(self) -> None:
        self.items: dict[Broker, BrokerCredentials] = {}

    async def save(self, credentials: BrokerCredentials) -> None:
        self.items[credentials.broker] = credentials

    async def get_credentials(self, broker: Broker) -> BrokerCredentials | None:
        return self.items.get(broker)

    async def delete(self, broker: Broker) -> None:
        self.items.pop(broker, None)


class FakeCredentialsUnitOfWork(FakePriceSyncUnitOfWork):
    def __init__(self) -> None:
        super().__init__()
        self.credentials = InMemoryCredentials()
