import pytest

from app.modules.identity.application.register_user import RegisterUser
from app.modules.identity.domain.user import EmailAlreadyRegisteredError
from app.modules.identity.infrastructure.persistence import Argon2PasswordHasher
from app.shared.domain.rates import RateType
from fakes.identity import FakeHasher, FakeUnitOfWork


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


async def test_argon2_verify() -> None:
    hasher = Argon2PasswordHasher()
    password_hash = await hasher.hash("clave-larga-123")

    assert await hasher.verify("clave-larga-123", password_hash)
    assert not await hasher.verify("otra-clave-456", password_hash)
    # Sin hash (usuario inexistente) igual calcula, pero nunca valida.
    assert not await hasher.verify("clave-larga-123", None)
