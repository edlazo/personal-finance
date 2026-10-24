"""Repositorio, Unit of Work y hashing de identity."""

import asyncio
import secrets
from functools import cache
from typing import Self

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.domain.user import EmailAlreadyRegisteredError, User
from app.modules.identity.infrastructure.models import UserModel
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def _to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        name=model.name,
        password_hash=model.password_hash,
        default_rate_type=model.default_rate_type,
        created_at=model.created_at,
    )


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        model = await self._session.scalar(select(UserModel).where(UserModel.email == email))
        return None if model is None else _to_domain(model)

    async def add(self, user: User) -> None:
        self._session.add(
            UserModel(
                id=user.id,
                email=user.email,
                name=user.name,
                password_hash=user.password_hash,
                default_rate_type=user.default_rate_type,
                created_at=user.created_at,
            )
        )
        try:
            await self._session.flush()
        except IntegrityError as exc:
            # Dos registros simultáneos con el mismo email: los frena el índice único.
            raise EmailAlreadyRegisteredError from exc


class SqlAlchemyIdentityUnitOfWork(SqlAlchemyUnitOfWork):
    users: SqlAlchemyUserRepository

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self.users = SqlAlchemyUserRepository(self.session)
        return self


_hasher = PasswordHash((Argon2Hasher(),))


@cache
def _dummy_hash() -> str:
    # Se calcula una vez por proceso; sirve para verificar cuando el usuario no existe.
    return _hasher.hash(secrets.token_urlsafe(16))


class Argon2PasswordHasher:
    # Argon2 usa CPU a propósito: en un thread para no bloquear el event loop.
    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(_hasher.hash, password)

    async def verify(self, password: str, password_hash: str | None) -> bool:
        target = (
            password_hash if password_hash is not None else await asyncio.to_thread(_dummy_hash)
        )
        valid = await asyncio.to_thread(_hasher.verify, password, target)
        return valid and password_hash is not None
