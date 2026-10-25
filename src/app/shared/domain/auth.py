"""Tokens de acceso: los emite identity y los valida cualquier módulo."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.shared.domain.errors import UnauthorizedError


@dataclass(frozen=True)
class RefreshClaims:
    """Lo que identity guarda de cada refresh token para poder rotarlo y revocarlo."""

    user_id: UUID
    jti: str
    expires_at: datetime


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int
    refresh: RefreshClaims


class InvalidTokenError(UnauthorizedError):
    def __init__(self) -> None:
        super().__init__("Token inválido o vencido")
