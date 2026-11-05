from collections.abc import Callable, Iterator
from datetime import datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from pydantic import PostgresDsn
from sqlalchemy.ext.asyncio import AsyncEngine
from structlog.testing import capture_logs

from app.config import Settings
from app.main import create_app
from app.modules.ledger.infrastructure.jobs import generate_recurring
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
        email = f"recurrentes-{uuid4().hex[:8]}@example.com"
        client.post("/auth/register", json={"email": email, "password": PASSWORD, "name": "Ana"})
        login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    return create


def test_recurring_rules_crud_and_pause(
    client: TestClient, sign_up: Callable[[], dict[str, str]]
) -> None:
    ana = sign_up()
    pesos = {"name": "Galicia", "type": "SAVINGS", "currency": "ARS", "initial_balance": "0"}
    account = client.post("/accounts", headers=ana, json=pesos).json()["id"]
    garage = {"name": "Cochera", "kind": "EXPENSE"}
    category = client.post("/categories", headers=ana, json=garage).json()["id"]
    body = {
        "account_id": account,
        "kind": "EXPENSE",
        "amount": "500000",
        "category_id": category,
        "frequency": "MONTHLY",
        "start_date": "2026-11-10",
        "end_date": "2027-10-10",
        "description": "Cochera del depto",
    }

    created = client.post("/recurring", headers=ana, json=body)
    url = f"/recurring/{created.json()['id']}"
    edited = client.patch(url, headers=ana, json={"paused": True, "end_date": None}).json()

    assert created.status_code == 201
    assert (edited["paused"], edited["end_date"], edited["amount"]) == (True, None, "500000.00")
    assert client.get("/recurring", headers=ana).json() == [edited]
    for wrong in ({"kind": "INCOME"}, {"frequency": "DAILY"}):
        assert client.post("/recurring", headers=ana, json=body | wrong).status_code == 422
    assert client.patch(url, headers=ana, json={"amount": "0"}).status_code == 422
    assert client.get(url, headers=sign_up()).status_code == 404
    assert client.delete(url, headers=ana).status_code == 204
    assert client.get(url, headers=ana).status_code == 404


async def test_the_job_generates_movements_and_pending_ones_once(
    client: TestClient, sign_up: Callable[[], dict[str, str]], engine: AsyncEngine
) -> None:
    ana = sign_up()
    pesos = {"name": "Galicia", "type": "SAVINGS", "currency": "ARS", "initial_balance": "900000"}
    account = client.post("/accounts", headers=ana, json=pesos).json()["id"]
    empty = client.post("/accounts", headers=ana, json=pesos | {"name": "Vacía"}).json()["id"]
    garage = client.post("/categories", headers=ana, json={"name": "Cochera", "kind": "EXPENSE"})
    tz = ZoneInfo("America/Argentina/Buenos_Aires")
    today = datetime.now(tz).date()
    weekly = {
        "account_id": account,
        "kind": "EXPENSE",
        "amount": "100000",
        "category_id": garage.json()["id"],
        "frequency": "WEEKLY",
        "start_date": str(today - timedelta(days=14)),
    }
    client.post("/recurring", headers=ana, json=weekly)
    client.post("/recurring", headers=ana, json=weekly | {"needs_confirmation": True})
    skipped = client.post("/recurring", headers=ana, json=weekly | {"account_id": empty}).json()
    client.delete(f"/accounts/{empty}", headers=ana)

    with capture_logs() as logs:
        for _ in range(2):
            await generate_recurring(create_session_factory(engine), tz)

    movements = client.get("/transactions", headers=ana).json()
    pending = client.get("/recurring/pending", headers=ana).json()
    assert movements["total"] == 3
    assert [p["date"] for p in pending] == [str(today - timedelta(days=d)) for d in (14, 7, 0)]
    # La cuenta archivada frena su regla, sin cortar las demás.
    skips = [log["rule_id"] for log in logs if log["event"] == "recurring_rule_skipped"]
    assert skips.count(skipped["id"]) == 2

    first, second = (f"/recurring/pending/{p['id']}" for p in pending[:2])
    confirmed = client.post(f"{first}/confirm", headers=ana, json={"amount": "95000.50"})
    assert (confirmed.status_code, confirmed.json()["amount"]) == (201, "95000.50")
    assert client.delete(second, headers=ana).status_code == 204
    assert len(client.get("/recurring/pending", headers=ana).json()) == 1
    assert client.post(f"{second}/confirm", headers=ana, json={}).status_code == 404
    assert client.get("/recurring/pending", headers=sign_up()).json() == []
