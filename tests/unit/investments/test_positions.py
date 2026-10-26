from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.modules.investments.application.list_positions import ListPositions
from app.modules.investments.domain.instrument import Instrument, InstrumentType, Market
from app.modules.investments.domain.position import build_positions
from app.modules.investments.domain.price import InstrumentPrice
from app.modules.investments.domain.trade import Trade, TradeSide
from app.shared.domain.money import Currency
from app.shared.domain.rates import RateType
from fakes.investments import FakeInvestmentsUnitOfWork

USER, BROKER, OTHER = uuid4(), uuid4(), uuid4()
BUY, SELL = TradeSide.BUY, TradeSide.SELL
GGAL = Instrument(USER, "GGAL", "Galicia", InstrumentType.STOCK, Market.BYMA, Currency.ARS)
AL30 = Instrument(USER, "AL30", "Bonar 2030", InstrumentType.BOND, Market.BYMA, Currency.ARS)


def trade(
    instrument: Instrument, side: TradeSide, qty: str, price: str, fee: str = "0", day: int = 1
) -> Trade:
    return Trade(
        USER,
        BROKER,
        instrument.id,
        side,
        Decimal(qty),
        Decimal(price),
        Decimal(fee),
        date(2026, 10, day),
    )


def test_weighted_average_cost_with_fees_and_realized_pnl_on_sell() -> None:
    trades = [
        trade(GGAL, SELL, "5", "130", fee="5", day=3),
        trade(GGAL, BUY, "10", "100", fee="10", day=1),
        trade(GGAL, BUY, "10", "120", day=2),
        trade(AL30, BUY, "1000", "75000"),
    ]

    al30, ggal = build_positions(trades, {GGAL.id: GGAL, AL30.id: AL30})

    assert (ggal.quantity, ggal.cost, ggal.realized_pnl) == (
        Decimal("15"),
        Decimal("1657.50"),
        Decimal("92.50"),
    )
    assert (ggal.average_price, ggal.current_price, ggal.valuation) == (
        Decimal("110.5"),
        Decimal("130"),
        Decimal("1950.00"),
    )
    assert (ggal.unrealized_pnl, ggal.unrealized_pnl_pct) == (Decimal("292.50"), Decimal("17.65"))
    # Bonos: precio cada 100 VN.
    assert (al30.average_price, al30.valuation) == (Decimal("75000"), Decimal("750000.00"))


def test_positions_are_per_account_and_closed_ones_keep_their_result() -> None:
    elsewhere = trade(GGAL, BUY, "2", "100")
    elsewhere.account_id = OTHER
    trades = [trade(GGAL, BUY, "1", "10"), trade(GGAL, SELL, "1", "12", day=2), elsewhere]

    by_account = {p.account_id: p for p in build_positions(trades, {GGAL.id: GGAL})}

    closed, other = by_account[BROKER], by_account[OTHER]
    assert (closed.quantity, closed.realized_pnl) == (Decimal("0"), Decimal("2"))
    assert (closed.average_price, closed.unrealized_pnl_pct) == (Decimal("0"), Decimal("0"))
    assert other.quantity == Decimal("2")


class ThousandPesosPerDollar:
    async def convert(
        self,
        amount: Decimal,
        source: Currency,
        target: Currency,
        *,
        rate_type: RateType,
        at: datetime,
    ) -> Decimal:
        return amount if source is target else amount / 1000


class PrefersBlue:
    async def default_rate_type(self, user_id: UUID) -> RateType:
        return RateType.BLUE


async def test_positions_are_valued_in_ars_and_usd() -> None:
    uow = FakeInvestmentsUnitOfWork()
    uow.instruments.items.append(GGAL)
    uow.trades.items.append(trade(GGAL, BUY, "10", "1000"))

    used, [valued] = await ListPositions(uow, ThousandPesosPerDollar(), PrefersBlue())(USER)

    assert (used, valued.valuation_ars, valued.valuation_usd) == (
        RateType.BLUE,
        Decimal("10000.00"),
        Decimal("10"),
    )


def test_the_most_recent_price_wins_and_manual_wins_a_tie() -> None:
    trades = [trade(GGAL, BUY, "1", "100", day=10)]

    def priced(day: int) -> tuple[Decimal, str]:
        manual = InstrumentPrice(USER, GGAL.id, Decimal("150"), date(2026, 10, day))
        [position] = build_positions(trades, {GGAL.id: GGAL}, {GGAL.id: manual})
        return position.current_price, position.price_source

    assert priced(11) == (Decimal("150"), "MANUAL")
    assert priced(10) == (Decimal("150"), "MANUAL")
    assert priced(9) == (Decimal("100"), "LAST_TRADE")
