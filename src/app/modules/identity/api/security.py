"""Autenticación de los endpoints protegidos (Bearer JWT)."""

from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings
from app.modules.identity.domain.user import InvalidTokenError
from app.modules.identity.infrastructure.tokens import JwtTokenService

# auto_error=False: sin header respondemos nosotros, como problem+json con WWW-Authenticate.
bearer = HTTPBearer(auto_error=False)


def get_token_service(request: Request) -> JwtTokenService:
    settings: Settings = request.app.state.settings
    return JwtTokenService(
        settings.jwt_secret.get_secret_value(),
        access_ttl=timedelta(minutes=settings.access_token_minutes),
        refresh_ttl=timedelta(days=settings.refresh_token_days),
    )


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    tokens: Annotated[JwtTokenService, Depends(get_token_service)],
) -> UUID:
    if credentials is None:
        raise InvalidTokenError
    return tokens.decode_access(credentials.credentials)
