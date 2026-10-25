import os
import subprocess
import sys
from collections.abc import AsyncIterator, Callable, Iterator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine
from testcontainers.community.postgres import PostgresContainer

from app.shared.infrastructure.database import create_engine

POSTGRES_IMAGE = "postgres:17-alpine"
ROOT = Path(__file__).parents[2]

Alembic = Callable[..., subprocess.CompletedProcess[str]]


def run_alembic(database_url: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - comando fijo, sin input externo
        [sys.executable, "-m", "alembic", "-x", f"url={database_url}", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    # En el CI la base es un service de GitHub Actions; en local, un contenedor efímero.
    if url := os.environ.get("TEST_DATABASE_URL"):
        yield url
        return
    with PostgresContainer(POSTGRES_IMAGE, driver="asyncpg") as postgres:
        yield postgres.get_connection_url()


@pytest.fixture
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_engine(database_url)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
def alembic() -> Alembic:
    return run_alembic


@pytest.fixture(scope="session")
def migrated_database_url(database_url: str) -> str:
    result = run_alembic(database_url, "upgrade", "head")
    assert result.returncode == 0, result.stderr
    return database_url
