"""Worker de jobs programados: `python -m app.worker`."""

import asyncio
import contextlib
import signal

from apscheduler.schedulers.asyncio import AsyncIOScheduler


def create_scheduler() -> AsyncIOScheduler:
    # Los jobs de cada módulo (cotizaciones, recurrentes, snapshots) se registran acá.
    return AsyncIOScheduler()


async def run(stop: asyncio.Event) -> None:
    scheduler = create_scheduler()
    scheduler.start()
    try:
        await stop.wait()
    finally:
        scheduler.shutdown()


async def serve() -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    # En Windows no hay signal handlers en asyncio; ahí Ctrl+C corta con KeyboardInterrupt.
    with contextlib.suppress(NotImplementedError):
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop.set)
    await run(stop)


if __name__ == "__main__":
    asyncio.run(serve())
