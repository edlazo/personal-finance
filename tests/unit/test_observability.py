from collections.abc import Iterator

import pytest
import structlog
from fastapi.testclient import TestClient
from structlog.testing import capture_logs

from app.config import Settings
from app.main import create_app
from app.shared.domain.errors import ConflictError, DomainError, NotFoundError

PROBLEM_JSON = "application/problem+json"


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    app = create_app(settings)

    @app.get("/test/not-found")
    async def not_found() -> None:
        raise NotFoundError("La cuenta no existe")

    @app.get("/test/conflict")
    async def conflict() -> None:
        raise ConflictError("El email ya está registrado")

    @app.get("/test/domain")
    async def domain() -> None:
        raise DomainError("Saldo insuficiente")

    @app.get("/test/items")
    async def items(qty: int) -> dict[str, int]:
        return {"qty": qty}

    @app.get("/test/boom")
    async def boom() -> None:
        raise RuntimeError("detalle interno secreto")

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.mark.parametrize(
    ("path", "status", "detail"),
    [
        ("/test/not-found", 404, "La cuenta no existe"),
        ("/test/conflict", 409, "El email ya está registrado"),
        ("/test/domain", 422, "Saldo insuficiente"),
    ],
)
def test_domain_errors_are_problem_json(
    client: TestClient, path: str, status: int, detail: str
) -> None:
    response = client.get(path)

    assert response.status_code == status
    assert response.headers["content-type"] == PROBLEM_JSON
    body = response.json()
    assert body["status"] == status
    assert body["detail"] == detail
    assert body["request_id"] == response.headers["x-request-id"]


def test_validation_error_lists_fields(client: TestClient) -> None:
    response = client.get("/test/items", params={"qty": "muchos"})

    assert response.status_code == 422
    assert response.headers["content-type"] == PROBLEM_JSON
    assert response.json()["errors"][0]["loc"] == ["query", "qty"]


def test_unknown_route_is_problem_json(client: TestClient) -> None:
    response = client.get("/no-existe")

    assert response.status_code == 404
    assert response.json()["title"] == "Not Found"


def test_unhandled_error_hides_details_and_logs(client: TestClient) -> None:
    with capture_logs() as logs:
        response = client.get("/test/boom")

    assert response.status_code == 500
    assert response.json()["detail"] == "Error interno"
    assert "secreto" not in response.text
    assert any(log["event"] == "unhandled_error" for log in logs)


def test_request_is_logged_with_request_id(client: TestClient) -> None:
    with capture_logs(processors=[structlog.contextvars.merge_contextvars]) as logs:
        response = client.get("/test/items", params={"qty": 2})

    [log] = [log for log in logs if log["event"] == "request"]
    assert log["method"] == "GET"
    assert log["path"] == "/test/items"
    assert log["status"] == 200
    assert log["duration_ms"] >= 0
    assert log["request_id"] == response.headers["x-request-id"]


@pytest.mark.parametrize(
    ("incoming", "reused"),
    [("abc-123.DEF_4", True), ("con espacios", False), ("x" * 65, False)],
)
def test_request_id_header(client: TestClient, incoming: str, reused: bool) -> None:
    returned = client.get("/test/items", params={"qty": 1}, headers={"X-Request-ID": incoming})
    request_id = returned.headers["x-request-id"]

    assert (request_id == incoming) is reused
    if not reused:
        assert len(request_id) == 32
