"""Jobs del worker: precios de cripto desde CoinGecko."""

from datetime import datetime
from zoneinfo import ZoneInfo

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.modules.investments.application.sync_crypto_prices import SyncCryptoPrices
from app.modules.investments.domain.price import PriceProvider
from app.modules.investments.infrastructure.persistence import SqlAlchemyPriceSyncUnitOfWork

logger = structlog.get_logger()


async def sync_crypto_prices(
    session_factory: async_sessionmaker[AsyncSession], provider: PriceProvider, tz: ZoneInfo
) -> None:
    sync = SyncCryptoPrices(SqlAlchemyPriceSyncUnitOfWork(session_factory), provider)
    try:
        saved = await sync(datetime.now(tz).date())
    except Exception:
        # Queda el último precio guardado; el próximo turno vuelve a intentar.
        logger.exception("crypto_prices_sync_failed")
        return
    logger.info("crypto_prices_synced", saved=saved)


def schedule_investment_jobs(
    scheduler: AsyncIOScheduler,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    provider: PriceProvider,
) -> None:
    # Cripto opera todo el día: cada hora en punto (decisión del PO).
    tz = ZoneInfo(settings.fx_timezone)
    hourly = CronTrigger(minute=0, timezone=tz)
    scheduler.add_job(
        sync_crypto_prices, hourly, args=[session_factory, provider, tz], id="crypto_prices"
    )
