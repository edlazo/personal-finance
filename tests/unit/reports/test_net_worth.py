from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.modules.reports.application.net_worth import GetNetWorth
from app.shared.domain.money import Currency
from app.shared.domain.net_worth import NetWorthGroup, NetWorthItem, NetWorthSource
from app.shared.domain.rates import RateType

ARS, USD = Currency.ARS, Currency.USD


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
        if source is target:
            return amount
        return amount / 1000 if source is ARS else amount * 1000


class PrefersBlue:
    async def default_rate_type(self, user_id: UUID) -> RateType:
        return RateType.BLUE


def source(*items: NetWorthItem) -> NetWorthSource:
    async def report() -> list[NetWorthItem]:
        return list(items)

    return report


async def test_assets_minus_liabilities_by_group_and_currency() -> None:
    sources = [
        source(
            NetWorthItem(NetWorthGroup.ACCOUNTS, ARS, Decimal("500000")),
            NetWorthItem(NetWorthGroup.ACCOUNTS, USD, Decimal("100")),
        ),
        source(NetWorthItem(NetWorthGroup.CARDS, ARS, Decimal("30000"))),
    ]
    get = GetNetWorth(sources, ThousandPesosPerDollar(), PrefersBlue())

    report = await get(uuid4(), [ARS, USD])
    in_dollars = await get(uuid4(), [USD], rate_type=RateType.MEP)

    accounts, investments, *_ = report.groups
    assert accounts.by_currency == {ARS: Decimal("500000"), USD: Decimal("100")}
    assert accounts.total == {ARS: Decimal("600000"), USD: Decimal("600")}
    assert (investments.by_currency, investments.total[ARS]) == ({}, Decimal("0"))
    assert report.rate_type is RateType.BLUE
    assert report.liabilities == {ARS: Decimal("30000"), USD: Decimal("30")}
    assert report.net_worth == {ARS: Decimal("570000"), USD: Decimal("570")}
    assert (in_dollars.rate_type, in_dollars.net_worth) == (RateType.MEP, {USD: Decimal("570")})
