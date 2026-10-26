import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest

from app import worker


async def test_run_starts_and_stops_scheduler() -> None:
    stop = asyncio.Event()
    task = asyncio.create_task(worker.run(stop))
    await asyncio.sleep(0)

    stop.set()
    await asyncio.wait_for(task, timeout=1)

    assert task.done()
    assert task.exception() is None


async def test_serve_runs_until_stopped(monkeypatch: pytest.MonkeyPatch) -> None:
    received: list[asyncio.Event] = []

    async def fake_run(stop: asyncio.Event) -> None:
        received.append(stop)

    monkeypatch.setattr(worker, "run", fake_run)

    await worker.serve()

    assert len(received) == 1


def test_the_worker_registers_every_table_its_jobs_reference() -> None:
    # En un proceso limpio: en este, otros tests ya importaron los modelos de identity.
    # sorted_tables resuelve todas las claves foráneas: falla si falta alguna tabla.
    check = "import app.worker; from app.shared.infrastructure.database import Base; "
    check += "Base.metadata.sorted_tables"
    src = str(Path(__file__).parents[2] / "src")
    result = subprocess.run(  # noqa: S603 (comando fijo)
        [sys.executable, "-c", check],
        capture_output=True,
        text=True,
        env=os.environ | {"PYTHONPATH": src},
    )
    assert result.returncode == 0, result.stderr
