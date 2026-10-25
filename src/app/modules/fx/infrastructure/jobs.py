"""Jobs del worker: cotizaciones automáticas desde dolarapi."""

from zoneinfo import ZoneInfo

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.modules.fx.application.sync_rates import SyncRates
from app.modules.fx.domain.rate import ExchangeRateProvider
from app.modules.fx.infrastructure.persistence import SqlAlchemyFxUnitOfWork

logger = structlog.get_logger()


async def sync_rates(
    session_factory: async_sessionmaker[AsyncSession], provider: ExchangeRateProvider
) -> None:
    try:
        saved = await SyncRates(
            uow=SqlAlchemyFxUnitOfWork(session_factory, None), provider=provider
        )()
    except Exception:
        # Se conserva el último valor guardado; el próximo turno vuelve a intentar.
        logger.exception("fx_sync_failed")
        return
    logger.info("fx_synced", saved=saved)


def schedule_fx_jobs(
    scheduler: AsyncIOScheduler,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    provider: ExchangeRateProvider,
) -> None:
    # shortcut: los feriados cuentan como días hábiles; agregar un calendario si molesta.
    tz = ZoneInfo(settings.fx_timezone)
    args = [session_factory, provider]
    business = CronTrigger(
        day_of_week="mon-fri", hour=settings.fx_business_hours, minute="*/30", timezone=tz
    )
    weekend = CronTrigger(day_of_week="sat,sun", hour=settings.fx_daily_hour, timezone=tz)
    scheduler.add_job(sync_rates, business, args=args, id="fx_business_hours")
    scheduler.add_job(sync_rates, weekend, args=args, id="fx_weekend")
