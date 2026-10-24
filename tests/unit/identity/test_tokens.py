from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.modules.identity.domain.user import InvalidTokenError
from app.modules.identity.infrastructure.tokens import JwtTokenService

SECRET = "x" * 32


def service(clock: datetime | None = None, secret: str = SECRET) -> JwtTokenService:
    now = clock or datetime.now(UTC)
    return JwtTokenService(secret, timedelta(minutes=15), timedelta(days=7), clock=lambda: now)


def test_access_token_lasts_15_minutes_and_refresh_7_days() -> None:
    user_id = uuid4()
    tokens = service().issue(user_id)

    access = jwt.decode(tokens.access_token, SECRET, algorithms=["HS256"])
    refresh = jwt.decode(tokens.refresh_token, SECRET, algorithms=["HS256"])
    assert access["exp"] - access["iat"] == 15 * 60
    assert refresh["exp"] - refresh["iat"] == 7 * 24 * 3600
    assert tokens.expires_in == 900
    assert service().decode_access(tokens.access_token) == user_id


def test_refresh_token_is_not_an_access_token() -> None:
    tokens = service().issue(uuid4())

    with pytest.raises(InvalidTokenError):
        service().decode_access(tokens.refresh_token)


@pytest.mark.parametrize(
    "token",
    [
        service(clock=datetime.now(UTC) - timedelta(hours=1)).issue(uuid4()).access_token,
        service(secret="y" * 32).issue(uuid4()).access_token,
        "no-es-un-jwt",
    ],
    ids=["vencido", "otra-clave", "basura"],
)
def test_invalid_tokens_are_rejected(token: str) -> None:
    with pytest.raises(InvalidTokenError):
        service().decode_access(token)
