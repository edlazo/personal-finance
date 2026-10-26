"""Casos de uso: guardar, consultar y borrar las credenciales de un broker."""

import json
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.modules.investments.domain.credentials import (
    Broker,
    BrokerCredentials,
    CredentialCipher,
    CredentialsRepository,
    InvalidCredentialsError,
    mask,
)
from app.shared.application.unit_of_work import UnitOfWork


class CredentialsUnitOfWork(UnitOfWork, Protocol):
    @property
    def credentials(self) -> CredentialsRepository: ...


@dataclass(frozen=True)
class SaveCredentials:
    """Decisión del PO: se guardan sin verificarlas contra el broker (no gasta cupo de IOL)."""

    uow: CredentialsUnitOfWork
    cipher: CredentialCipher

    async def __call__(self, user_id: UUID, broker: Broker, username: str, password: str) -> None:
        username = username.strip()
        if not username or not password:
            raise InvalidCredentialsError("El usuario y la contraseña son obligatorios")
        login = json.dumps({"username": username, "password": password}).encode()
        stored = BrokerCredentials(user_id, broker, mask(username), self.cipher.encrypt(login))
        async with self.uow:
            await self.uow.credentials.save(stored)
            await self.uow.commit()


@dataclass(frozen=True)
class CredentialsStatus:
    uow: CredentialsUnitOfWork

    async def __call__(self, broker: Broker) -> BrokerCredentials | None:
        async with self.uow:
            return await self.uow.credentials.get_credentials(broker)


@dataclass(frozen=True)
class DeleteCredentials:
    uow: CredentialsUnitOfWork

    async def __call__(self, broker: Broker) -> None:
        async with self.uow:
            await self.uow.credentials.delete(broker)
            await self.uow.commit()
