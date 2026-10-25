"""Worker de jobs programados: `python -m app.worker`."""

import asyncio
import contextlib
import signal

import httpx2
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.modules.fx.infrastructure.dolarapi import DolarApiProvider
from app.modules.fx.infrastructure.jobs import schedule_fx_jobs
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
        schedule_fx_jobs(scheduler, settings, create_session_factory(engine), provider)
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
