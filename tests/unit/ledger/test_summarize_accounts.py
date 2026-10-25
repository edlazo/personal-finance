from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.modules.ledger.application.summarize_accounts import SummarizeAccounts
from app.modules.ledger.domain.account import Account, AccountType
from app.shared.domain.money import Currency
from app.shared.domain.rates import RateType
from fakes.accounts import FakeAccountsUnitOfWork

USER = uuid4()


class ThousandPesosPerDollar:
    def __init__(self) -> None:
        self.rate_types: set[RateType] = set()

    async def convert(
        self,
        amount: Decimal,
        source: Currency,
        target: Currency,
        *,
        rate_type: RateType,
        at: datetime,
    ) -> Decimal:
        self.rate_types.add(rate_type)
        if source is target:
            return amount
        return amount / 1000 if source is Currency.ARS else amount * 1000


class PrefersBlue:
    async def default_rate_type(self, user_id: UUID) -> RateType:
        return RateType.BLUE


async def test_each_account_and_the_total_in_both_currencies() -> None:
    uow = FakeAccountsUnitOfWork()
    for name, currency, initial in (
        ("Galicia", Currency.ARS, "50000"),
        ("Dólares", Currency.USD, "100"),
    ):
        account = Account(USER, name, AccountType.SAVINGS, currency, Decimal(initial))
        uow.accounts.items[account.id] = account
    uow.accounts.totals[account.id] = Decimal("20")  # movimientos de la cuenta en USD
    converter = ThousandPesosPerDollar()
    summarize = SummarizeAccounts(uow, converter, PrefersBlue())

    summary = await summarize(USER)

    rows = [(a.item.account.name, a.ars, a.usd) for a in summary.accounts]
    assert rows == [
        ("Galicia", Decimal("50000"), Decimal("50")),
        ("Dólares", Decimal("120000"), Decimal("120")),
    ]
    assert (summary.rate_type, summary.total_ars, summary.total_usd) == (
        RateType.BLUE,
        Decimal("170000"),
        Decimal("170"),
    )
    assert (await summarize(USER, rate_type=RateType.MEP)).rate_type is RateType.MEP
    assert converter.rate_types == {RateType.BLUE, RateType.MEP}
