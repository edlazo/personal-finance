"""Dobles en memoria para los casos de uso de identity."""

from types import TracebackType
from typing import Self

from app.modules.identity.domain.user import User


class InMemoryUsers:
    def __init__(self) -> None:
        self.by_email: dict[str, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        return self.by_email.get(email)

    async def add(self, user: User) -> None:
        self.by_email[user.email] = user


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.users = InMemoryUsers()
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
