from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config import Settings
from app.modules.ledger.infrastructure.jobs import schedule_ledger_jobs


def test_recurring_runs_every_day_and_when_the_worker_starts() -> None:
    scheduler = AsyncIOScheduler()

    schedule_ledger_jobs(scheduler, Settings(_env_file=None), async_sessionmaker())

    (job,) = scheduler.get_jobs()
    assert (job.id, "hour='0', minute='5'" in str(job.trigger)) == ("recurring", True)
    assert job.next_run_time <= datetime.now(UTC)
