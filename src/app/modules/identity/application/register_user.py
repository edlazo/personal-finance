"""Caso de uso: registrar un usuario."""

from dataclasses import dataclass
from typing import Protocol

from app.modules.identity.domain.user import (
    EmailAlreadyRegisteredError,
    PasswordHasher,
    User,
    UserRepository,
    normalize_email,
)
from app.shared.application.unit_of_work import UnitOfWork


class IdentityUnitOfWork(UnitOfWork, Protocol):
    @property
    def users(self) -> UserRepository: ...


@dataclass(frozen=True)
class RegisterUser:
    uow: IdentityUnitOfWork
    hasher: PasswordHasher

    async def __call__(self, *, email: str, password: str, name: str) -> User:
        email = normalize_email(email)
        # Se hashea antes de abrir la transacción para no retener la conexión durante el cálculo.
        password_hash = await self.hasher.hash(password)
        async with self.uow:
            if await self.uow.users.get_by_email(email) is not None:
                raise EmailAlreadyRegisteredError
            user = User(email=email, name=name, password_hash=password_hash)
            await self.uow.users.add(user)
            await self.uow.commit()
        return user
