from collections.abc import Callable, Iterator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import PostgresDsn
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import Settings
from app.main import create_app
from app.modules.ledger.domain.category import default_categories
from app.modules.ledger.infrastructure.persistence import SqlAlchemyLedgerUnitOfWork
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
def sign_up(client: TestClient) -> Callable[[], tuple[UUID, dict[str, str]]]:
    """Registra un usuario nuevo y devuelve su id y el header con su access token."""

    def create() -> tuple[UUID, dict[str, str]]:
        email = f"categorias-{uuid4().hex[:8]}@example.com"
        user = client.post(
            "/auth/register", json={"email": email, "password": PASSWORD, "name": "Ana"}
        )
        login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
        return UUID(user.json()["id"]), {"Authorization": f"Bearer {login.json()['access_token']}"}

    return create


def test_first_get_creates_defaults_once_and_per_user(
    client: TestClient, sign_up: Callable[[], tuple[UUID, dict[str, str]]]
) -> None:
    _, ana = sign_up()
    _, beto = sign_up()

    first = client.get("/categories", headers=ana).json()
    second = client.get("/categories", headers=ana).json()
    other = client.get("/categories", headers=beto).json()

    assert len(first) == 13
    assert {c["kind"] for c in first if c["name"] == "Otros"} == {"INCOME", "EXPENSE"}
    assert second == first
    assert not {c["id"] for c in other} & {c["id"] for c in first}


async def test_simultaneous_first_uses_do_not_duplicate(
    client: TestClient,
    sign_up: Callable[[], tuple[UUID, dict[str, str]]],
    engine: AsyncEngine,
) -> None:
    user_id, auth = sign_up()
    session_factory = create_session_factory(engine)
    # Simula dos pedidos que vieron "sin categorías" a la vez: el segundo no debe fallar.
    for _ in range(2):
        async with SqlAlchemyLedgerUnitOfWork(session_factory, user_id) as uow:
            await uow.categories.add_defaults(default_categories(user_id))
            await uow.commit()

    assert len(client.get("/categories", headers=auth).json()) == 13


def test_categories_require_a_token(client: TestClient) -> None:
    assert client.get("/categories").status_code == 401
