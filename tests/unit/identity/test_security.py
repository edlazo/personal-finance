from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID, uuid4

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.modules.identity.api.security import get_current_user_id
from app.modules.identity.infrastructure.tokens import JwtTokenService


def tokens_for(settings: Settings, clock: datetime | None = None) -> JwtTokenService:
    now = clock or datetime.now(UTC)
    return JwtTokenService(
        settings.jwt_secret.get_secret_value(),
        timedelta(minutes=settings.access_token_minutes),
        timedelta(days=settings.refresh_token_days),
        clock=lambda: now,
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    app = create_app(settings)

    @app.get("/test/protegido")
    async def protected(user_id: Annotated[UUID, Depends(get_current_user_id)]) -> str:
        return str(user_id)

    with TestClient(app) as client:
        yield client


def test_valid_access_token_identifies_the_user(client: TestClient, settings: Settings) -> None:
    user_id = uuid4()
    token = tokens_for(settings).issue(user_id).access_token

    response = client.get("/test/protegido", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == str(user_id)


@pytest.mark.parametrize("case", ["sin-header", "vencido", "refresh"])
def test_protected_endpoint_rejects_missing_expired_or_refresh_tokens(
    client: TestClient, settings: Settings, case: str
) -> None:
    past = datetime.now(UTC) - timedelta(hours=1)
    tokens = tokens_for(settings, clock=past if case == "vencido" else None).issue(uuid4())
    token = tokens.refresh_token if case == "refresh" else tokens.access_token
    headers = {} if case == "sin-header" else {"Authorization": f"Bearer {token}"}

    response = client.get("/test/protegido", headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["detail"] == "Token inválido o vencido"
