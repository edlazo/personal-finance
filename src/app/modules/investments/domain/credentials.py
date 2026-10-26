"""Credenciales de un broker (IOL), guardadas cifradas."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from app.shared.domain.errors import DomainError


class Broker(StrEnum):
    IOL = "IOL"


class InvalidCredentialsError(DomainError):
    pass


def mask(username: str) -> str:
    """Pista para mostrar sin revelar el usuario: las dos primeras letras."""
    return f"{username[:2]}***"


@dataclass
class BrokerCredentials:
    """`secret` es el usuario y la contraseña cifrados: nunca se guardan ni devuelven en claro."""

    user_id: UUID
    broker: Broker
    username_hint: str
    secret: bytes = field(repr=False)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class CredentialCipher(Protocol):
    def encrypt(self, data: bytes) -> bytes: ...

    def decrypt(self, token: bytes) -> bytes: ...


class CredentialsRepository(Protocol):
    async def save(self, credentials: BrokerCredentials) -> None:
        """Guarda o reemplaza las del usuario para ese broker."""
        ...

    async def get_credentials(self, broker: Broker) -> BrokerCredentials | None: ...

    async def delete(self, broker: Broker) -> None: ...
