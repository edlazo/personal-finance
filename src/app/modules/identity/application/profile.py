"""Casos de uso: ver el perfil y cambiar las preferencias."""

from dataclasses import dataclass
from uuid import UUID

from app.modules.identity.application.register_user import IdentityUnitOfWork
from app.modules.identity.domain.user import User
from app.shared.domain.auth import InvalidTokenError
from app.shared.domain.rates import RateType


async def _existing_user(uow: IdentityUnitOfWork, user_id: UUID) -> User:
    user = await uow.users.get_by_id(user_id)
    if user is None:
        # El token es válido pero el usuario ya no existe: la sesión no sirve más.
        raise InvalidTokenError
    return user


@dataclass(frozen=True)
class GetProfile:
    uow: IdentityUnitOfWork

    async def __call__(self, user_id: UUID) -> User:
        async with self.uow:
            return await _existing_user(self.uow, user_id)


@dataclass(frozen=True)
class UpdatePreferences:
    uow: IdentityUnitOfWork

    async def __call__(self, user_id: UUID, *, default_rate_type: RateType) -> User:
        async with self.uow:
            user = await _existing_user(self.uow, user_id)
            user.default_rate_type = default_rate_type
            await self.uow.users.save_preferences(user)
            await self.uow.commit()
        return user


@dataclass(frozen=True)
class UserRatePreference:
    """Implementa `RatePreference` (app.shared) para los otros módulos."""

    uow: IdentityUnitOfWork

    async def default_rate_type(self, user_id: UUID) -> RateType:
        return (await GetProfile(uow=self.uow)(user_id)).default_rate_type
