import json
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.investments.application.sync_portfolio import SyncPortfolio
from app.modules.investments.domain.credentials import Broker, BrokerCredentials, BrokerLink
from app.modules.investments.domain.instrument import Instrument, InstrumentType, Market
from app.modules.investments.domain.portfolio import BrokerHolding, CallBudgetExhaustedError
from app.shared.domain.money import Currency
from fakes.investments import FakeInvestmentsUnitOfWork

USER, IOL = uuid4(), uuid4()
NOW = datetime(2026, 10, 26, 15, 30, tzinfo=UTC)
GGAL = Instrument(USER, "GGAL", "Galicia", InstrumentType.STOCK, Market.BYMA, Currency.ARS)
HOLDINGS = [
    BrokerHolding(
        "ggal",
        "Galicia",
        InstrumentType.STOCK,
        Market.BYMA,
        Currency.ARS,
        *[Decimal(n) for n in ("10", "6000", "6500")],
    ),
    BrokerHolding(
        "AL30",
        "Bonar",
        InstrumentType.BOND,
        Market.BYMA,
        Currency.ARS,
        *[Decimal(n) for n in ("1000", "70000", "75000")],
    ),
]


class PlainCipher:
    def encrypt(self, data: bytes) -> bytes:
        return data

    def decrypt(self, token: bytes) -> bytes:
        return token


class FakeIol:
    def __init__(self) -> None:
        self.logins: list[tuple[str, str]] = []

    async def portfolio(self, username: str, password: str) -> list[BrokerHolding]:
        self.logins.append((username, password))
        return HOLDINGS


def linked_user() -> FakeInvestmentsUnitOfWork:
    uow = FakeInvestmentsUnitOfWork()
    uow.instruments.items.append(GGAL)
    uow.links.items[Broker.IOL] = BrokerLink(USER, Broker.IOL, IOL)
    secret = json.dumps({"username": "elias", "password": "clave"}).encode()
    uow.credentials.items[Broker.IOL] = BrokerCredentials(USER, Broker.IOL, "el***", secret)
    return uow


async def test_the_snapshot_replaces_the_last_one_and_new_tickers_join_the_catalog() -> None:
    uow, iol = linked_user(), FakeIol()
    sync = SyncPortfolio(uow, iol, PlainCipher(), monthly_limit=20_000)

    assert await sync(USER, NOW) == await sync(USER, NOW) == 2

    by_ticker = {i.id: i.ticker for i in uow.instruments.items}
    assert sorted(by_ticker.values()) == ["AL30", "GGAL"]
    assert [(by_ticker[s.instrument_id], s.account_id) for s in uow.snapshots.items] == [
        ("GGAL", IOL),
        ("AL30", IOL),
    ]
    assert iol.logins == [("elias", "clave")] * 2
    assert uow.budget.calls == {(Broker.IOL, date(2026, 10, 1)): 4}


async def test_the_sync_stops_at_the_monthly_call_limit() -> None:
    uow, iol = linked_user(), FakeIol()
    sync = SyncPortfolio(uow, iol, PlainCipher(), monthly_limit=3)
    await sync(USER, NOW)

    with pytest.raises(CallBudgetExhaustedError):
        await sync(USER, NOW)
    # El mes siguiente arranca con el cupo entero.
    assert await sync(USER, datetime(2026, 11, 1, tzinfo=UTC)) == 2
    assert len(iol.logins) == 2


async def test_without_a_linked_account_iol_is_not_called() -> None:
    uow, iol = linked_user(), FakeIol()
    uow.links.items.clear()

    assert await SyncPortfolio(uow, iol, PlainCipher(), monthly_limit=10)(USER, NOW) is None
    assert (iol.logins, uow.budget.calls) == ([], {})
