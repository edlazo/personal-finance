"""Usuario y reglas de identidad."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from app.shared.domain.auth import TokenPair
from app.shared.domain.errors import ConflictError, UnauthorizedError
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


class InvalidCredentialsError(UnauthorizedError):
    def __init__(self) -> None:
        # El mismo mensaje para email inexistente o contraseña incorrecta.
        super().__init__("Email o contraseña incorrectos")


class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None: ...

    async def add(self, user: User) -> None: ...


class PasswordHasher(Protocol):
    async def hash(self, password: str) -> str: ...

    async def verify(self, password: str, password_hash: str | None) -> bool:
        """Con `password_hash=None` igual hace el cálculo y devuelve False (mismo tiempo)."""
        ...


class TokenService(Protocol):
    def issue(self, user_id: UUID) -> TokenPair: ...

    def decode_access(self, token: str) -> UUID: ...
