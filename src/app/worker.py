"""Worker de jobs programados: `python -m app.worker`."""

import asyncio
import contextlib
import signal

import httpx2
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Los jobs guardan filas con claves foráneas a users y accounts: sin esas tablas en la metadata,
# SQLAlchemy no puede resolverlas y el insert falla.
import app.modules.identity.infrastructure.models
import app.modules.ledger.infrastructure.accounts
import app.modules.ledger.infrastructure.persistence  # noqa: F401
from app.config import get_settings
from app.modules.fx.infrastructure.dolarapi import DolarApiProvider
from app.modules.fx.infrastructure.jobs import schedule_fx_jobs
from app.modules.investments.infrastructure.coingecko import CoinGeckoProvider
from app.modules.investments.infrastructure.data912 import Data912Provider
from app.modules.investments.infrastructure.iol import IolClient
from app.modules.investments.infrastructure.jobs import schedule_investment_jobs
from app.modules.ledger.infrastructure.cash_movements import LedgerCashMovements
from app.shared.infrastructure.database import create_engine, create_session_factory
from app.shared.infrastructure.logging import configure_logging

logger = structlog.get_logger()


def create_scheduler() -> AsyncIOScheduler:
    # Los jobs de cada módulo (cotizaciones, recurrentes, snapshots) se registran acá.
    return AsyncIOScheduler()


async def run(stop: asyncio.Event) -> None:
    settings = get_settings()
    engine = create_engine(str(settings.database_url))
    async with httpx2.AsyncClient() as client:
        scheduler = create_scheduler()
        provider = DolarApiProvider(client, settings.dolarapi_url)
        session_factory = create_session_factory(engine)
        schedule_fx_jobs(scheduler, settings, session_factory, provider)
        key = settings.coingecko_api_key
        coingecko = CoinGeckoProvider(
            client, settings.coingecko_url, api_key=key.get_secret_value() if key else None
        )
        iol = IolClient(client, settings.iol_url)
        schedule_investment_jobs(
            scheduler,
            settings,
            session_factory,
            coingecko,
            iol,
            LedgerCashMovements,
            Data912Provider(client, settings.data912_url),
        )
        scheduler.start()
        logger.info("worker_started")
        try:
            await stop.wait()
        finally:
            scheduler.shutdown()
            await engine.dispose()
            logger.info("worker_stopped")


async def serve() -> None:
    configure_logging(json_logs=get_settings().environment != "local")
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    # En Windows no hay signal handlers en asyncio; ahí Ctrl+C corta con KeyboardInterrupt.
    with contextlib.suppress(NotImplementedError):
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop.set)
    await run(stop)


if __name__ == "__main__":
    asyncio.run(serve())
