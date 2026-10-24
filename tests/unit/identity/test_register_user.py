from types import TracebackType
from typing import Self

import pytest

from app.modules.identity.application.register_user import RegisterUser
from app.modules.identity.domain.user import EmailAlreadyRegisteredError, User
from app.modules.identity.infrastructure.persistence import Argon2PasswordHasher
from app.shared.domain.rates import RateType


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


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


async def test_registers_user_with_normalized_email_and_mep(uow: FakeUnitOfWork) -> None:
    register = RegisterUser(uow=uow, hasher=FakeHasher())

    user = await register(email="  Elias@Example.COM ", password="clave-larga-123", name="Elias")

    assert user.email == "elias@example.com"
    assert user.password_hash == "hashed:clave-larga-123"
    assert user.default_rate_type is RateType.MEP
    assert uow.users.by_email["elias@example.com"] is user
    assert uow.committed


async def test_rejects_registered_email_ignoring_case(uow: FakeUnitOfWork) -> None:
    register = RegisterUser(uow=uow, hasher=FakeHasher())
    await register(email="elias@example.com", password="clave-larga-123", name="Elias")
    uow.committed = False

    with pytest.raises(EmailAlreadyRegisteredError):
        await register(email="ELIAS@example.com", password="otra-clave-456", name="Otro")
    assert not uow.committed


async def test_argon2_hasher_uses_argon2id() -> None:
    password_hash = await Argon2PasswordHasher().hash("clave-larga-123")

    assert password_hash.startswith("$argon2id$")
    assert "clave-larga-123" not in password_hash
