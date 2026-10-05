import asyncio

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
