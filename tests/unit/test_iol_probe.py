from pathlib import Path

import httpx2
import pytest

import iol_probe

TITLES = {"titulos": [{"simbolo": "GGAL", "ultimoPrecio": 6500, "moneda": "peso_Argentino"}]}


def iol(calls: list[str]) -> httpx2.MockTransport:
    """Primero el access token está vencido; renovar entrega un par nuevo."""

    def handle(request: httpx2.Request) -> httpx2.Response:
        calls.append(request.url.path)
        if request.url.path == "/token":
            return httpx2.Response(
                200, json={"access_token": "nuevo-a", "refresh_token": "nuevo-r"}
            )
        if request.headers["Authorization"] == "Bearer viejo-a":
            return httpx2.Response(401)
        if "portafolio" in request.url.path:
            return httpx2.Response(200, json={"activos": [{"cantidad": 10, "valorizado": 1}]})
        if "Todos" in request.url.path:
            return httpx2.Response(200, json=TITLES)
        return httpx2.Response(200, json={"ultimoPrecio": 6500, "moneda": "peso_Argentino"})

    return httpx2.MockTransport(handle)


def test_renews_the_token_stays_within_the_cap_and_never_prints_secrets(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    env = tmp_path / ".env"
    env.write_text(
        "OTRA=1\nIOL_ACCESS_TOKEN=viejo-a\nIOL_REFRESH_TOKEN=viejo-r\n", encoding="utf-8"
    )
    calls: list[str] = []

    iol_probe.main(env, iol(calls))

    out = capsys.readouterr().out
    assert len(calls) == iol_probe.MAX_CALLS
    assert iol_probe.read_env(env) == {
        "OTRA": "1",
        "IOL_ACCESS_TOKEN": "nuevo-a",
        "IOL_REFRESH_TOKEN": "nuevo-r",
    }
    assert not any(secret in out for secret in ("viejo-a", "viejo-r", "nuevo-a", "nuevo-r"))
    assert "Posiciones: 1" in out


def test_the_budget_stops_before_going_over() -> None:
    budget = iol_probe.CallBudget(1)
    budget.spend()
    with pytest.raises(SystemExit, match="Tope"):
        budget.spend()
