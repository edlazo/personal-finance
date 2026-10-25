from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from pydantic import PostgresDsn
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import Settings
from app.main import create_app
from app.modules.fx.domain.rate import ExchangeRate, RateSource
from app.modules.fx.infrastructure.persistence import ExchangeRateModel, SqlAlchemyFxUnitOfWork
from app.shared.domain.rates import RateType
from app.shared.infrastructure.database import create_session_factory

pytestmark = pytest.mark.integration

PASSWORD = "clave-larga-123"


@pytest.fixture
def client(migrated_database_url: str) -> Iterator[TestClient]:
    settings = Settings(
        _env_file=None, environment="test", database_url=PostgresDsn(migrated_database_url)
    )
    with TestClient(create_app(settings)) as client:
        yield client


@pytest.fixture
def sign_up(client: TestClient) -> Callable[[], dict[str, str]]:
    def create() -> dict[str, str]:
        email = f"cotizaciones-{uuid4().hex[:8]}@example.com"
        client.post("/auth/register", json={"email": email, "password": PASSWORD, "name": "Ana"})
        login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    return create


def post_rate(client: TestClient, auth: dict[str, str], **fields: Any) -> Response:
    body = {
        "type": "MEP",
        "buy": "1180.5",
        "sell": "1200.1234567891",
        "quoted_at": "2026-10-24T15:00:00-03:00",
    }
    return client.post("/fx/rates", headers=auth, json=body | fields)


async def test_manual_rates_are_stored_without_overwriting(
    client: TestClient, sign_up: Callable[[], dict[str, str]], engine: AsyncEngine
) -> None:
    auth = sign_up()

    first = post_rate(client, auth)
    second = post_rate(client, auth, sell="1210")

    assert first.status_code == second.status_code == 201
    assert (first.json()["sell"], first.json()["source"]) == ("1200.1234567891", "MANUAL")
    ids = [first.json()["id"], second.json()["id"]]
    async with engine.connect() as connection:
        count = select(func.count()).where(ExchangeRateModel.id.in_(ids))
        assert await connection.scalar(count) == 2


def test_invalid_or_anonymous_rates_are_rejected(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    auth = sign_up()

    assert post_rate(client, {}).status_code == 401
    assert post_rate(client, auth, buy="0").status_code == 422
    assert post_rate(client, auth, quoted_at="2026-10-24T15:00:00").status_code == 422
    assert post_rate(client, auth, type="EURO").status_code == 422


async def test_latest_and_history_show_api_rates_and_only_my_manual_ones(
    client: TestClient, sign_up: Callable[[], dict[str, str]], engine: AsyncEngine
) -> None:
    ana, beto = sign_up(), sign_up()
    # Fechas desde ahora: la base de los tests se comparte y puede tener otras cotizaciones.
    base = datetime.now(UTC) + timedelta(days=1)
    later, earlier = base + timedelta(hours=1), base
    newest = post_rate(client, ana, sell="1300", quoted_at=later.isoformat()).json()
    older = post_rate(client, ana, sell="1250", quoted_at=earlier.isoformat()).json()
    post_rate(client, beto, sell="9999", quoted_at=(later + timedelta(hours=1)).isoformat())
    api = ExchangeRate(RateType.CCL, Decimal("1290"), Decimal("1310"), later, RateSource.API)
    async with SqlAlchemyFxUnitOfWork(create_session_factory(engine), uuid4()) as uow:
        await uow.rates.add(api)
        await uow.commit()

    latest = {r["type"]: r for r in client.get("/fx/rates/latest", headers=ana).json()}
    history = client.get("/fx/rates", headers=ana, params={"type": "MEP"}).json()
    window = {"type": "MEP", "from": earlier.isoformat(), "to": earlier.isoformat()}
    only_earlier = client.get("/fx/rates", headers=ana, params=window).json()

    assert (latest["MEP"]["id"], latest["CCL"]["id"]) == (newest["id"], str(api.id))
    assert [r["id"] for r in history][:2] == [newest["id"], older["id"]]
    assert [r["id"] for r in only_earlier] == [older["id"]]
    assert "9999" not in {r["sell"] for r in history}
    everything = client.get("/fx/rates", headers=ana).json()
    assert {newest["id"], str(api.id)} <= {r["id"] for r in everything}
    assert client.get("/fx/rates", headers=ana, params={"from": "2026-10-24"}).status_code == 422
