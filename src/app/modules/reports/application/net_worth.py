"""Caso de uso: el patrimonio neto de hoy, sumando lo que informa cada módulo (US-047)."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.modules.reports.domain.net_worth import GroupTotal, NetWorthReport
from app.shared.domain.money import Currency
from app.shared.domain.net_worth import LIABILITIES, NetWorthGroup, NetWorthSource
from app.shared.domain.rates import MoneyConverter, RatePreference, RateType

ZERO = Decimal("0.00")


@dataclass(frozen=True)
class GetNetWorth:
    sources: list[NetWorthSource]
    converter: MoneyConverter
    preference: RatePreference

    async def __call__(
        self, user_id: UUID, currencies: list[Currency], *, rate_type: RateType | None = None
    ) -> NetWorthReport:
        """Decisión del PO: solo hoy; el histórico sale de una foto diaria en otra historia."""
        rate_type = rate_type or await self.preference.default_rate_type(user_id)
        at = datetime.now(UTC)
        origin: dict[NetWorthGroup, dict[Currency, Decimal]] = {g: {} for g in NetWorthGroup}
        for source in self.sources:
            for item in await source():
                totals = origin[item.group]
                totals[item.currency] = totals.get(item.currency, ZERO) + item.amount

        async def convert(totals: dict[Currency, Decimal], target: Currency) -> Decimal:
            amounts = [
                await self.converter.convert(a, c, target, rate_type=rate_type, at=at)
                for c, a in totals.items()
            ]
            return sum(amounts, ZERO)

        groups = [
            GroupTotal(g, totals, {c: await convert(totals, c) for c in currencies})
            for g, totals in origin.items()
        ]

        def total(liability: bool) -> dict[Currency, Decimal]:
            chosen = [g for g in groups if (g.group in LIABILITIES) is liability]
            return {c: sum((g.total[c] for g in chosen), ZERO) for c in currencies}

        assets, liabilities = total(False), total(True)
        net = {c: assets[c] - liabilities[c] for c in currencies}
        return NetWorthReport(rate_type, groups, assets, liabilities, net)
