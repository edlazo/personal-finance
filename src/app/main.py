"""Punto de entrada de la API: `fastapi dev src/app/main.py`."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.shared.api.health import router as health_router
from app.shared.infrastructure.database import create_engine, create_session_factory


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
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
    app.state.settings = settings
    app.include_router(health_router)
    return app


app = create_app()
