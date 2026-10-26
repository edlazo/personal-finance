from decimal import Decimal
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import async_sessionmaker
from structlog.testing import capture_logs

from app.config import Settings
from app.modules.investments.infrastructure.jobs import (
    schedule_investment_jobs,
    sync_crypto_prices,
)
from app.shared.domain.money import Currency


class BrokenProvider:
    async def prices(self, tickers: set[str]) -> dict[str, dict[Currency, Decimal]]:
        raise RuntimeError("CoinGecko no responde")


async def test_a_failing_job_is_logged_and_keeps_the_last_price() -> None:
    with capture_logs() as logs:
        await sync_crypto_prices(async_sessionmaker(), BrokenProvider(), ZoneInfo("UTC"))

    assert [log["event"] for log in logs] == ["crypto_prices_sync_failed"]


def test_crypto_prices_run_every_hour() -> None:
    scheduler = AsyncIOScheduler()

    schedule_investment_jobs(
        scheduler, Settings(_env_file=None), async_sessionmaker(), BrokenProvider()
    )

    [job] = scheduler.get_jobs()
    assert (job.id, "minute='0'" in str(job.trigger)) == ("crypto_prices", True)
