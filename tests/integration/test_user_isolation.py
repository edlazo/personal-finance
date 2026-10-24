from collections.abc import AsyncIterator, Iterator
from typing import Annotated
from uuid import UUID, uuid4

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from pydantic import PostgresDsn
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped

from app.config import Settings
from app.main import create_app
from app.shared.api.auth import CurrentUserId
from app.shared.api.dependencies import get_session_factory
from app.shared.infrastructure.database import Base, create_session_factory
from app.shared.infrastructure.user_scoped import UserOwnedMixin, UserScopedRepository

pytestmark = pytest.mark.integration

PASSWORD = "clave-larga-123"


class Note(UserOwnedMixin, Base):
    """Recurso de prueba: los módulos reales (cuentas, movimientos...) siguen el mismo patrón."""

    __tablename__ = "test_isolation_notes"
    text: Mapped[str]


class NoteRepository(UserScopedRepository[Note]):
    model = Note


@pytest.fixture
async def notes_table(migrated_database_url: str, engine: AsyncEngine) -> AsyncIterator[None]:
    table = Base.metadata.tables[Note.__tablename__]
    async with engine.begin() as connection:
        await connection.run_sync(table.create)
    yield
    async with engine.begin() as connection:
        await connection.run_sync(table.drop)


@pytest.fixture
def client(migrated_database_url: str, notes_table: None) -> Iterator[TestClient]:
    settings = Settings(
        _env_file=None, environment="test", database_url=PostgresDsn(migrated_database_url)
    )
    app = create_app(settings)

    @app.get("/test/notas/{note_id}")
    async def get_note(
        note_id: UUID,
        user_id: CurrentUserId,
        session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
    ) -> str:
        async with session_factory() as session:
            return (await NoteRepository(session, user_id).get(note_id)).text

    with TestClient(app) as client:
        yield client


def sign_up(client: TestClient) -> tuple[UUID, dict[str, str]]:
    """Registra un usuario y devuelve su id y el header con su access token."""
    email = f"aislamiento-{uuid4().hex[:8]}@example.com"
    registered = client.post(
        "/auth/register", json={"email": email, "password": PASSWORD, "name": "Usuario"}
    )
    login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    token = login.json()["access_token"]
    return UUID(registered.json()["id"]), {"Authorization": f"Bearer {token}"}


async def test_user_b_gets_404_on_user_a_resources(client: TestClient, engine: AsyncEngine) -> None:
    user_a, headers_a = sign_up(client)
    user_b, headers_b = sign_up(client)
    note_id = uuid4()
    async with create_session_factory(engine)() as session:
        session.add(Note(id=note_id, user_id=user_a, text="nota de A"))
        await session.commit()

    own = client.get(f"/test/notas/{note_id}", headers=headers_a)
    foreign = client.get(f"/test/notas/{note_id}", headers=headers_b)

    assert own.status_code == 200
    assert own.json() == "nota de A"
    assert foreign.status_code == 404
    assert foreign.headers["content-type"] == "application/problem+json"
    async with create_session_factory(engine)() as session:
        assert await NoteRepository(session, user_b).list() == []
        assert [n.text for n in await NoteRepository(session, user_a).list()] == ["nota de A"]
