import subprocess
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from pydantic import PostgresDsn
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import Settings
from app.main import create_app
from app.shared.infrastructure.database import create_engine, ping

pytestmark = pytest.mark.integration

UNREACHABLE_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:1/nothing"


async def test_ping_ok(engine: AsyncEngine) -> None:
    assert await ping(engine) is True


async def test_ping_fails_when_database_unreachable() -> None:
    engine = create_engine(UNREACHABLE_URL)
    try:
        assert await ping(engine) is False
    finally:
        await engine.dispose()


def test_alembic_upgrade_and_check(
    migrated_database_url: str, alembic: Callable[..., subprocess.CompletedProcess[str]]
) -> None:
    # `migrated_database_url` ya corrió `alembic upgrade head`; acá se verifica que no falte nada.
    check = alembic(migrated_database_url, "check")
    assert check.returncode == 0, check.stdout + check.stderr


@pytest.mark.parametrize(
    ("url_fixture", "expected_status"),
    [("database_url", 200), (None, 503)],
)
def test_health_reports_database(
    request: pytest.FixtureRequest, url_fixture: str | None, expected_status: int
) -> None:
    url = request.getfixturevalue(url_fixture) if url_fixture else UNREACHABLE_URL
    settings = Settings(_env_file=None, environment="test", database_url=PostgresDsn(url))

    with TestClient(create_app(settings)) as client:
        response = client.get("/health")

    assert response.status_code == expected_status
