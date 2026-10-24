"""Usuario y reglas de identidad."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from app.shared.domain.errors import ConflictError
from app.shared.domain.rates import RateType

MIN_PASSWORD_LENGTH = 10
# Tope para no hashear entradas enormes (Argon2 es caro a propósito).
MAX_PASSWORD_LENGTH = 128


def normalize_email(email: str) -> str:
    return email.strip().lower()


@dataclass
class User:
    email: str
    name: str
    password_hash: str
    default_rate_type: RateType = RateType.MEP
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class EmailAlreadyRegisteredError(ConflictError):
    def __init__(self) -> None:
        super().__init__("El email ya está registrado")


class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None: ...

    async def add(self, user: User) -> None: ...


class PasswordHasher(Protocol):
    async def hash(self, password: str) -> str: ...
