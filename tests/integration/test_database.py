import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.shared.infrastructure.database import create_engine, ping

pytestmark = pytest.mark.integration

ROOT = Path(__file__).parents[2]
UNREACHABLE_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:1/nothing"


def alembic(database_url: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - comando fijo, sin input externo
        [sys.executable, "-m", "alembic", "-x", f"url={database_url}", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


async def test_ping_ok(engine: AsyncEngine) -> None:
    assert await ping(engine) is True


async def test_ping_fails_when_database_unreachable() -> None:
    engine = create_engine(UNREACHABLE_URL)
    try:
        assert await ping(engine) is False
    finally:
        await engine.dispose()


def test_alembic_upgrade_and_check(database_url: str) -> None:
    upgrade = alembic(database_url, "upgrade", "head")
    assert upgrade.returncode == 0, upgrade.stderr

    check = alembic(database_url, "check")
    assert check.returncode == 0, check.stderr
