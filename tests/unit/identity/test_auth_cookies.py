from collections.abc import Iterator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import Settings
from app.main import create_app
from app.modules.identity.api.routes import get_identity_uow, get_login_user
from app.modules.identity.application.login_user import LoginUser
from app.modules.identity.domain.user import User
from app.shared.infrastructure.tokens import JwtTokenService
from fakes.identity import FakeHasher, FakeUnitOfWork

PASSWORD = "clave-larga-123"
CREDENTIALS = {"email": "ana@example.com", "password": PASSWORD}


def make_client(settings: Settings) -> TestClient:
    """La app real, con los casos de uso apoyados en dobles en memoria (sin base de datos)."""
    app = create_app(settings)
    uow = FakeUnitOfWork()
    user = User(email="ana@example.com", name="Ana", password_hash=f"hashed:{PASSWORD}")
    uow.users.by_email[user.email] = user
    tokens = JwtTokenService(
        settings.jwt_secret.get_secret_value(), timedelta(minutes=15), timedelta(days=7)
    )
    app.dependency_overrides[get_identity_uow] = lambda: uow
    app.dependency_overrides[get_login_user] = lambda: LoginUser(
        uow=uow, hasher=FakeHasher(), tokens=tokens
    )
    return TestClient(app)


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with make_client(settings) as client:
        yield client


def test_login_puts_the_refresh_token_only_in_an_httponly_cookie(client: TestClient) -> None:
    response = client.post("/auth/login", json=CREDENTIALS)

    assert set(response.json()) == {"access_token", "token_type", "expires_in"}
    cookie = response.headers["set-cookie"]
    assert cookie.startswith("refresh_token=")
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert "Max-Age=604800" in cookie
    assert "Secure" not in cookie


def test_refresh_rotates_the_cookie_and_the_old_one_stops_working(client: TestClient) -> None:
    client.post("/auth/login", json=CREDENTIALS)
    old = client.cookies["refresh_token"]

    rotated = client.post("/auth/refresh")
    client.cookies.set("refresh_token", old)
    reused = client.post("/auth/refresh")

    assert rotated.status_code == 200
    assert "access_token" in rotated.json()
    assert rotated.cookies["refresh_token"] != old
    assert reused.status_code == 401


def test_refresh_without_cookie_is_401(client: TestClient) -> None:
    assert client.post("/auth/refresh").status_code == 401


def test_logout_revokes_and_deletes_the_cookie(client: TestClient) -> None:
    client.post("/auth/login", json=CREDENTIALS)
    session = client.cookies["refresh_token"]

    logout = client.post("/auth/logout")
    client.cookies.set("refresh_token", session)
    after = client.post("/auth/refresh")

    assert logout.status_code == 204
    assert 'refresh_token=""' in logout.headers["set-cookie"]
    assert after.status_code == 401
    client.cookies.clear()
    assert client.post("/auth/logout").status_code == 204


def test_the_cookie_is_secure_in_production() -> None:
    settings = Settings(
        _env_file=None,
        environment="production",
        jwt_secret=SecretStr("una-clave-de-produccion-de-32-caracteres"),
        credentials_key=SecretStr("PEoYk1W6c1r0Xk5lTE7rVQzp3o3t5TQxZb0fJ0r9mUo="),
    )
    with make_client(settings) as client:
        response = client.post("/auth/login", json=CREDENTIALS)

    assert "Secure" in response.headers["set-cookie"]
