"""Caso de uso: iniciar sesión."""

from dataclasses import dataclass

from app.modules.identity.application.register_user import IdentityUnitOfWork
from app.modules.identity.domain.user import (
    InvalidCredentialsError,
    PasswordHasher,
    TokenService,
    normalize_email,
)
from app.shared.domain.auth import TokenPair


@dataclass(frozen=True)
class LoginUser:
    uow: IdentityUnitOfWork
    hasher: PasswordHasher
    tokens: TokenService

    async def __call__(self, *, email: str, password: str) -> TokenPair:
        async with self.uow:
            user = await self.uow.users.get_by_email(normalize_email(email))
        # Se verifica aunque el usuario no exista: así el tiempo no revela qué emails hay.
        valid = await self.hasher.verify(password, user.password_hash if user else None)
        if user is None or not valid:
            raise InvalidCredentialsError
        tokens = self.tokens.issue(user.id)
        async with self.uow:
            await self.uow.refresh_tokens.add(tokens.refresh)
            await self.uow.commit()
        return tokens
