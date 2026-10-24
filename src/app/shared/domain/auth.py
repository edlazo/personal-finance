"""Tokens de acceso: los emite identity y los valida cualquier módulo."""

from dataclasses import dataclass

from app.shared.domain.errors import UnauthorizedError


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


class InvalidTokenError(UnauthorizedError):
    def __init__(self) -> None:
        super().__init__("Token inválido o vencido")
