"""Punto de entrada de la API: `fastapi dev src/app/main.py`."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.modules.fx.api.routes import router as fx_router
from app.modules.fx.application.currency_converter import CurrencyConverter
from app.modules.fx.infrastructure.persistence import SqlAlchemyFxUnitOfWork
from app.modules.identity.api.routes import me_router
from app.modules.identity.api.routes import router as auth_router
from app.modules.identity.application.profile import UserRatePreference
from app.modules.identity.infrastructure.persistence import SqlAlchemyIdentityUnitOfWork
from app.modules.investments.api.routes import router as instruments_router
from app.modules.investments.api.routes import trades_router
from app.modules.ledger.api.accounts import router as accounts_router
from app.modules.ledger.api.routes import router as categories_router
from app.modules.ledger.api.transactions import router as transactions_router
from app.modules.ledger.api.transfers import router as transfers_router
from app.modules.ledger.infrastructure.cash_movements import LedgerCashMovements
from app.shared.api.health import router as health_router
from app.shared.api.middleware import request_logging
from app.shared.api.problems import register_problem_handlers
from app.shared.infrastructure.database import create_engine, create_session_factory
from app.shared.infrastructure.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Recursos compartidos: se abren antes del yield y se cierran después.
    settings: Settings = app.state.settings
    app.state.engine = create_engine(str(settings.database_url))
    app.state.session_factory = create_session_factory(app.state.engine)
    try:
        yield
    finally:
        await app.state.engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(json_logs=settings.environment != "local")
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
    app.state.settings = settings
    # Contratos de app.shared que un módulo usa y otro implementa (ver shared/api/contracts.py).
    app.state.money_converter = lambda session_factory, user_id: CurrencyConverter(
        uow=SqlAlchemyFxUnitOfWork(session_factory, user_id)
    )
    app.state.rate_preference = lambda session_factory: UserRatePreference(
        uow=SqlAlchemyIdentityUnitOfWork(session_factory)
    )
    # Con la sesión de investments: la operación y su movimiento van en una transacción.
    app.state.cash_movements = LedgerCashMovements
    app.middleware("http")(request_logging)
    register_problem_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(me_router)
    app.include_router(accounts_router)
    app.include_router(categories_router)
    app.include_router(transactions_router)
    app.include_router(transfers_router)
    app.include_router(fx_router)
    app.include_router(instruments_router)
    app.include_router(trades_router)
    return app


app = create_app()
