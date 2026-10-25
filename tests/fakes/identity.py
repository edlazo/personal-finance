"""Dobles en memoria para los casos de uso de identity."""

from datetime import UTC, datetime, timedelta
from types import TracebackType
from typing import Self
from uuid import UUID, uuid4

from app.modules.identity.domain.user import User
from app.shared.domain.auth import RefreshClaims, TokenPair


class InMemoryUsers:
    def __init__(self) -> None:
        self.by_email: dict[str, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        return self.by_email.get(email)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return next((u for u in self.by_email.values() if u.id == user_id), None)

    async def add(self, user: User) -> None:
        self.by_email[user.email] = user

    async def save_preferences(self, user: User) -> None:
        self.by_email[user.email] = user


class InMemoryRefreshTokens:
    def __init__(self) -> None:
        self.active: dict[str, RefreshClaims] = {}
        self.revoked: set[str] = set()

    async def add(self, token: RefreshClaims) -> None:
        self.active[token.jti] = token

    async def revoke(self, jti: str) -> bool:
        if jti not in self.active:
            return False
        del self.active[jti]
        self.revoked.add(jti)
        return True


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.users = InMemoryUsers()
        self.refresh_tokens = InMemoryRefreshTokens()
        self.committed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass


class FakeHasher:
    async def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def __init__(self) -> None:
        self.verified_hashes: list[str | None] = []

    async def verify(self, password: str, password_hash: str | None) -> bool:
        self.verified_hashes.append(password_hash)
        return password_hash == f"hashed:{password}"


class FakeTokens:
    """El refresh token es "<user_id>:<jti>", para poder decodificarlo sin firmar nada."""

    def issue(self, user_id: UUID) -> TokenPair:
        refresh = RefreshClaims(user_id, uuid4().hex, datetime.now(UTC) + timedelta(days=7))
        return TokenPair(
            f"access-{user_id}", f"{user_id}:{refresh.jti}", expires_in=900, refresh=refresh
        )

    def decode_refresh(self, token: str) -> RefreshClaims:
        user_id, jti = token.split(":")
        return RefreshClaims(UUID(user_id), jti, datetime.now(UTC) + timedelta(days=7))
