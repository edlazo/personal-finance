import pytest

from app.modules.identity.application.login_user import LoginUser
from app.modules.identity.domain.user import InvalidCredentialsError, User
from fakes.identity import FakeHasher, FakeTokens, FakeUnitOfWork


@pytest.fixture
def hasher() -> FakeHasher:
    return FakeHasher()


@pytest.fixture
def login(hasher: FakeHasher) -> LoginUser:
    uow = FakeUnitOfWork()
    user = User(email="ana@example.com", name="Ana", password_hash="hashed:clave-larga-123")
    uow.users.by_email[user.email] = user
    return LoginUser(uow=uow, hasher=hasher, tokens=FakeTokens())


async def test_valid_credentials_return_tokens(login: LoginUser) -> None:
    tokens = await login(email=" Ana@Example.com ", password="clave-larga-123")

    assert tokens.access_token.startswith("access-")
    assert tokens.expires_in == 900


async def test_wrong_password_and_unknown_email_fail_the_same_way(
    login: LoginUser, hasher: FakeHasher
) -> None:
    with pytest.raises(InvalidCredentialsError) as wrong_password:
        await login(email="ana@example.com", password="otra-clave-456")
    with pytest.raises(InvalidCredentialsError) as unknown_email:
        await login(email="nadie@example.com", password="clave-larga-123")

    assert str(wrong_password.value) == str(unknown_email.value)
    # Con un email inexistente igual se verifica (contra el hash de relleno).
    assert hasher.verified_hashes[-1] is None
