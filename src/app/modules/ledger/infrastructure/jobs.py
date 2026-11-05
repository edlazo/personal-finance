"""Job del worker: genera los movimientos de las reglas recurrentes."""

from datetime import datetime
from zoneinfo import ZoneInfo

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.modules.ledger.application.generate_recurring import GenerateRecurring
from app.modules.ledger.infrastructure.persistence import SqlAlchemyLedgerUnitOfWork
from app.modules.ledger.infrastructure.recurring import RecurringRuleModel
from app.shared.domain.errors import DomainError

logger = structlog.get_logger()


async def generate_recurring(
    session_factory: async_sessionmaker[AsyncSession], tz: ZoneInfo
) -> None:
    today = datetime.now(tz).date()
    async with session_factory() as session:
        rules = (
            await session.execute(select(RecurringRuleModel.user_id, RecurringRuleModel.id))
        ).all()
    for user_id, rule_id in rules:
        generate = GenerateRecurring(SqlAlchemyLedgerUnitOfWork(session_factory, user_id))
        try:
            created = await generate(rule_id, today)
        except DomainError as exc:
            # Cuenta archivada o sin saldo: la regla queda atrás y se reintenta mañana.
            logger.warning("recurring_rule_skipped", rule_id=str(rule_id), reason=str(exc))
        except Exception:
            logger.exception("recurring_rule_failed", rule_id=str(rule_id))
        else:
            if created:
                logger.info("recurring_generated", rule_id=str(rule_id), created=created)


def schedule_ledger_jobs(
    scheduler: AsyncIOScheduler,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    # Decisión del PO: todos los días a las 00:05 y al arrancar el worker (no duplica).
    tz = ZoneInfo(settings.fx_timezone)
    scheduler.add_job(
        generate_recurring,
        CronTrigger(hour=0, minute=5, timezone=tz),
        args=[session_factory, tz],
        id="recurring",
        next_run_time=datetime.now(tz),
    )
