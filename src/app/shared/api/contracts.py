"""Contratos entre módulos como dependencias de FastAPI.

Un módulo pide el contrato de app.shared y main.py guarda en `app.state` con qué
implementación se resuelve (decisión A4 del Sprint 5): así ningún módulo importa a otro.
"""

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.shared.api.auth import CurrentUserId
from app.shared.api.dependencies import get_session_factory
from app.shared.domain.rates import MoneyConverter, RatePreference

SessionFactory = Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)]
MoneyConverterFactory = Callable[[async_sessionmaker[AsyncSession], UUID], MoneyConverter]
RatePreferenceFactory = Callable[[async_sessionmaker[AsyncSession]], RatePreference]


def get_money_converter(
    request: Request, user_id: CurrentUserId, session_factory: SessionFactory
) -> MoneyConverter:
    factory: MoneyConverterFactory = request.app.state.money_converter
    return factory(session_factory, user_id)


def get_rate_preference(request: Request, session_factory: SessionFactory) -> RatePreference:
    factory: RatePreferenceFactory = request.app.state.rate_preference
    return factory(session_factory)


Converter = Annotated[MoneyConverter, Depends(get_money_converter)]
Preference = Annotated[RatePreference, Depends(get_rate_preference)]
