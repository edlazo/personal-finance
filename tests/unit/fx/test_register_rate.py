from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.fx.application.register_rate import RegisterManualRate
from app.modules.fx.domain.rate import ExchangeRate, InvalidRateError, RateSource
from app.shared.domain.rates import RateType
from fakes.fx import FakeFxUnitOfWork

USER = uuid4()
NOW = datetime(2026, 10, 24, 15, 0, tzinfo=UTC)


async def test_manual_rates_belong_to_the_user_and_keep_the_history() -> None:
    uow = FakeFxUnitOfWork()
    register = RegisterManualRate(uow=uow)

    await register(
        USER, rate_type=RateType.MEP, buy=Decimal("1180"), sell=Decimal("1200"), quoted_at=NOW
    )
    await register(
        USER, rate_type=RateType.MEP, buy=Decimal("1190"), sell=Decimal("1210"), quoted_at=NOW
    )

    assert [(r.sell, r.source, r.user_id) for r in uow.rates.items] == [
        (Decimal("1200"), RateSource.MANUAL, USER),
        (Decimal("1210"), RateSource.MANUAL, USER),
    ]
    assert uow.commits == 2


@pytest.mark.parametrize(
    ("buy", "quoted_at", "source", "match"),
    [
        ("0", NOW, RateSource.API, "mayores a cero"),
        ("1.12345678901", NOW, RateSource.API, "10 decimales"),
        ("1", datetime(2026, 10, 24, 15, 0), RateSource.API, "zona horaria"),  # noqa: DTZ001
        ("1", NOW, RateSource.MANUAL, "dueño"),
    ],
)
def test_rate_rules(buy: str, quoted_at: datetime, source: RateSource, match: str) -> None:
    with pytest.raises(InvalidRateError, match=match):
        ExchangeRate(RateType.BLUE, Decimal(buy), Decimal("1"), quoted_at, source)
