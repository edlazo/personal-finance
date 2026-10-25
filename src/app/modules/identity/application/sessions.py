"""Casos de uso: renovar la sesión y cerrarla."""

from dataclasses import dataclass

from app.modules.identity.application.register_user import IdentityUnitOfWork
from app.modules.identity.domain.user import TokenService
from app.shared.domain.auth import InvalidTokenError, TokenPair


@dataclass(frozen=True)
class RefreshSession:
    """Rota el refresh token: el usado queda revocado y se emite un par nuevo."""

    uow: IdentityUnitOfWork
    tokens: TokenService

    async def __call__(self, refresh_token: str) -> TokenPair:
        claims = self.tokens.decode_refresh(refresh_token)
        async with self.uow:
            if not await self.uow.refresh_tokens.revoke(claims.jti):
                raise InvalidTokenError
            tokens = self.tokens.issue(claims.user_id)
            await self.uow.refresh_tokens.add(tokens.refresh)
            await self.uow.commit()
        return tokens


@dataclass(frozen=True)
class Logout:
    uow: IdentityUnitOfWork
    tokens: TokenService

    async def __call__(self, refresh_token: str) -> None:
        claims = self.tokens.decode_refresh(refresh_token)
        async with self.uow:
            # Idempotente: cerrar una sesión ya cerrada no es un error.
            await self.uow.refresh_tokens.revoke(claims.jti)
            await self.uow.commit()
