from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.modules.investments.application.list_positions import ListPositions
from app.modules.investments.domain.credentials import Broker, BrokerLink
from app.modules.investments.domain.instrument import Instrument, InstrumentType, Market
from app.modules.investments.domain.portfolio import HoldingSnapshot
from app.modules.investments.domain.trade import Trade, TradeSide
from app.shared.domain.money import Currency
from app.shared.domain.rates import RateType
from fakes.investments import FakeInvestmentsUnitOfWork

USER, IOL, OTHER = uuid4(), uuid4(), uuid4()
GGAL = Instrument(USER, "GGAL", "Galicia", InstrumentType.STOCK, Market.BYMA, Currency.ARS)
AL30 = Instrument(USER, "AL30", "Bonar 2030", InstrumentType.BOND, Market.BYMA, Currency.ARS)


class SameCurrency:
    async def convert(
        self,
        amount: Decimal,
        source: Currency,
        target: Currency,
        *,
        rate_type: RateType,
        at: datetime,
    ) -> Decimal:
        return amount


class PrefersMep:
    async def default_rate_type(self, user_id: UUID) -> RateType:
        return RateType.MEP


def buy(account_id: UUID, qty: str) -> Trade:
    one, zero = Decimal("1"), Decimal("0")
    return Trade(
        USER, account_id, GGAL.id, TradeSide.BUY, Decimal(qty), one, zero, date(2026, 1, 2)
    )


async def test_the_linked_account_is_valued_from_the_broker_snapshot() -> None:
    uow = FakeInvestmentsUnitOfWork()
    uow.instruments.items += [GGAL, AL30]
    await uow.links.link(BrokerLink(USER, Broker.IOL, IOL))
    taken = datetime(2026, 10, 26, 15, 0, tzinfo=UTC)
    uow.snapshots.items += [
        HoldingSnapshot(USER, IOL, GGAL.id, Decimal("10"), Decimal("6000"), Decimal("6500"), taken),
        HoldingSnapshot(
            USER, IOL, AL30.id, Decimal("1000"), Decimal("70000"), Decimal("75000"), taken
        ),
        # Foto de una cuenta que se desvinculó: ya no cuenta.
        HoldingSnapshot(USER, OTHER, AL30.id, Decimal("5"), Decimal("1"), Decimal("1"), taken),
    ]
    # La operación cargada antes de vincular ya no cuenta; la de otra cuenta, sí.
    uow.trades.items += [buy(IOL, "99"), buy(OTHER, "2")]

    _, valued = await ListPositions(uow, SameCurrency(), PrefersMep())(USER)

    rows = {(v.position.instrument.ticker, v.position.account_id): v.position for v in valued}
    ggal, bond = rows[("GGAL", IOL)], rows[("AL30", IOL)]
    assert (ggal.quantity, ggal.cost, ggal.valuation) == (
        Decimal("10"),
        Decimal("60000.00"),
        Decimal("65000.00"),
    )
    assert (ggal.price_source, ggal.price_date, ggal.realized_pnl) == (
        "IOL",
        date(2026, 10, 26),
        Decimal("0.00"),
    )
    # Bonos: precios cada 100 VN.
    assert (bond.cost, bond.valuation) == (Decimal("700000.00"), Decimal("750000.00"))
    assert rows[("GGAL", OTHER)].quantity == Decimal("2")
    assert len(rows) == 3


async def test_an_empty_broker_portfolio_hides_the_trades_loaded_before() -> None:
    uow = FakeInvestmentsUnitOfWork()
    uow.instruments.items.append(GGAL)
    await uow.links.link(BrokerLink(USER, Broker.IOL, IOL))
    uow.trades.items.append(buy(IOL, "1"))

    assert await ListPositions(uow, SameCurrency(), PrefersMep())(USER) == (RateType.MEP, [])
