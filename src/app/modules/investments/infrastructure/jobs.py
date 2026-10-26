"""Jobs del worker: precios de cripto desde CoinGecko y portafolio de IOL."""

from datetime import datetime
from zoneinfo import ZoneInfo

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.modules.investments.application.sync_crypto_prices import SyncCryptoPrices
from app.modules.investments.application.sync_portfolio import SyncPortfolio
from app.modules.investments.domain.credentials import Broker, CredentialCipher
from app.modules.investments.domain.portfolio import CallBudgetExhaustedError, PortfolioClient
from app.modules.investments.domain.price import PriceProvider
from app.modules.investments.infrastructure.cipher import FernetCipher
from app.modules.investments.infrastructure.credentials import users_to_sync
from app.modules.investments.infrastructure.persistence import (
    CashMovementsFactory,
    SqlAlchemyInvestmentsUnitOfWork,
    SqlAlchemyPriceSyncUnitOfWork,
)

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


async def sync_iol_portfolios(
    session_factory: async_sessionmaker[AsyncSession],
    client: PortfolioClient,
    cipher: CredentialCipher,
    cash: CashMovementsFactory,
    monthly_limit: int,
    tz: ZoneInfo,
) -> None:
    async with session_factory() as session:
        users = await users_to_sync(session, Broker.IOL)
    now = datetime.now(tz)
    for user_id in users:
        uow = SqlAlchemyInvestmentsUnitOfWork(session_factory, user_id, cash)
        try:
            saved = await SyncPortfolio(uow, client, cipher, monthly_limit)(user_id, now)
        except CallBudgetExhaustedError:
            logger.warning("iol_call_budget_exhausted", user_id=str(user_id))
        except Exception:
            # Credenciales inválidas o IOL caído: queda la última foto y sigue con el resto.
            logger.exception("iol_portfolio_sync_failed", user_id=str(user_id))
        else:
            logger.info("iol_portfolio_synced", user_id=str(user_id), holdings=saved)


def schedule_investment_jobs(
    scheduler: AsyncIOScheduler,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    provider: PriceProvider,
    iol: PortfolioClient,
    cash: CashMovementsFactory,
) -> None:
    # Cripto opera todo el día: cada hora en punto (decisión del PO).
    tz = ZoneInfo(settings.fx_timezone)
    hourly = CronTrigger(minute=0, timezone=tz)
    scheduler.add_job(
        sync_crypto_prices, hourly, args=[session_factory, provider, tz], id="crypto_prices"
    )
    # Portafolio de IOL: días hábiles cada 30 minutos mientras opera BYMA (unas 600 llamadas
    # por mes, lejos del tope).
    rounds = CronTrigger(day_of_week="mon-fri", hour="11-17", minute="0,30", timezone=tz)
    cipher = FernetCipher(settings.credentials_key.get_secret_value())
    scheduler.add_job(
        sync_iol_portfolios,
        rounds,
        args=[session_factory, iol, cipher, cash, settings.iol_monthly_calls, tz],
        id="iol_portfolios",
    )
