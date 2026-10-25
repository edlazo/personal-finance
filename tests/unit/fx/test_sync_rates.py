from datetime import UTC, datetime, timedelta
from decimal import Decimal

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import async_sessionmaker
from structlog.testing import capture_logs

from app.config import Settings
from app.modules.fx.application.sync_rates import SyncRates
from app.modules.fx.domain.rate import ExchangeRate, RateSource
from app.modules.fx.infrastructure.jobs import schedule_fx_jobs, sync_rates
from app.shared.domain.rates import RateType
from fakes.fx import FakeFxUnitOfWork

AT = datetime(2026, 10, 24, 15, 0, tzinfo=UTC)


def mep(at: datetime) -> ExchangeRate:
    return ExchangeRate(RateType.MEP, Decimal("1480"), Decimal("1490"), at, RateSource.API)


class FixedProvider:
    def __init__(self, *rates: ExchangeRate) -> None:
        self.rates = list(rates)

    async def fetch(self) -> list[ExchangeRate]:
        return self.rates


class BrokenProvider:
    async def fetch(self) -> list[ExchangeRate]:
        raise RuntimeError("dolarapi no responde")


async def test_only_new_quotes_are_stored() -> None:
    uow = FakeFxUnitOfWork()
    provider = FixedProvider(mep(AT))
    sync = SyncRates(uow=uow, provider=provider)

    first, repeated = await sync(), await sync()
    provider.rates = [mep(AT + timedelta(minutes=30))]

    assert (first, repeated, await sync()) == (1, 0, 1)
    assert [r.quoted_at for r in uow.rates.items] == [AT, AT + timedelta(minutes=30)]


async def test_a_failing_source_is_logged_and_keeps_the_last_value() -> None:
    with capture_logs() as logs:
        await sync_rates(async_sessionmaker(), BrokenProvider())

    assert [log["event"] for log in logs] == ["fx_sync_failed"]


def test_jobs_run_on_business_hours_and_once_on_weekends() -> None:
    scheduler = AsyncIOScheduler()
    settings = Settings(_env_file=None, fx_business_hours="9-16", fx_daily_hour=11)

    schedule_fx_jobs(scheduler, settings, async_sessionmaker(), FixedProvider())

    triggers = {job.id: str(job.trigger) for job in scheduler.get_jobs()}
    assert "day_of_week='mon-fri', hour='9-16', minute='*/30'" in triggers["fx_business_hours"]
    assert "day_of_week='sat,sun', hour='11'" in triggers["fx_weekend"]
