"""Caso de uso: el saldo de cada cuenta y el total, en ARS y en USD."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.modules.ledger.application.create_account import AccountsUnitOfWork
from app.modules.ledger.application.manage_accounts import AccountBalance, ListAccounts
from app.shared.domain.money import Currency
from app.shared.domain.rates import MoneyConverter, RatePreference, RateType


@dataclass(frozen=True)
class AccountInBothCurrencies:
    item: AccountBalance
    ars: Decimal
    usd: Decimal


@dataclass(frozen=True)
class AccountsSummary:
    rate_type: RateType
    accounts: list[AccountInBothCurrencies]
    total_ars: Decimal
    total_usd: Decimal


@dataclass(frozen=True)
class SummarizeAccounts:
    uow: AccountsUnitOfWork
    converter: MoneyConverter
    preference: RatePreference

    async def __call__(
        self, user_id: UUID, *, rate_type: RateType | None = None
    ) -> AccountsSummary:
        rate_type = rate_type or await self.preference.default_rate_type(user_id)
        at = datetime.now(UTC)

        async def convert(item: AccountBalance, target: Currency) -> Decimal:
            return await self.converter.convert(
                item.balance, item.account.currency, target, rate_type=rate_type, at=at
            )

        accounts = [
            AccountInBothCurrencies(
                item, await convert(item, Currency.ARS), await convert(item, Currency.USD)
            )
            for item in await ListAccounts(uow=self.uow)()
        ]
        return AccountsSummary(
            rate_type,
            accounts,
            sum((a.ars for a in accounts), Decimal("0")),
            sum((a.usd for a in accounts), Decimal("0")),
        )
