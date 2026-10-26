"""Spike PF-48: prueba de solo lectura contra la API de IOL, con tope duro de llamadas.

Uso: guardá IOL_ACCESS_TOKEN e IOL_REFRESH_TOKEN en `.env` (está en .gitignore) y corré
`python scripts/iol_probe.py`. Nunca imprime los tokens ni los montos del portafolio. Si IOL
entrega tokens nuevos al renovar, los guarda en `.env` en lugar de los anteriores.
"""

from pathlib import Path
from typing import Any

import httpx2

BASE_URL = "https://api.invertironline.com"
# IOL cobra a partir de 25.000 llamadas por mes: la prueba no gasta más que esto.
MAX_CALLS = 5
LIMIT_HEADERS = ("limit", "quota", "remaining", "rate", "retry")


class CallBudget:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.used = 0

    def spend(self) -> None:
        if self.used >= self.limit:
            raise SystemExit(f"Tope de {self.limit} llamadas alcanzado: la prueba se corta.")
        self.used += 1


def read_env(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    pairs = (line.split("=", 1) for line in lines if "=" in line and not line.startswith("#"))
    return {key.strip(): value.strip() for key, value in pairs}


def write_env(path: Path, updates: dict[str, str]) -> None:
    """Reemplaza esas claves en `.env` y deja el resto del archivo como estaba."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    pending = dict(updates)
    for i, line in enumerate(lines):
        key = line.split("=", 1)[0].strip()
        if key in pending:
            lines[i] = f"{key}={pending.pop(key)}"
    lines += [f"{key}={value}" for key, value in pending.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def describe(name: str, response: httpx2.Response) -> None:
    print(f"\n{name}: HTTP {response.status_code}")
    headers = {
        k: v for k, v in response.headers.items() if any(h in k.lower() for h in LIMIT_HEADERS)
    }
    print(f"  Headers de límite: {headers or 'ninguno'}")
    if response.status_code != 200:
        return
    body: Any = response.json()
    if isinstance(body, dict) and "titulos" in body:
        titles = body["titulos"]
        print(f"  Títulos en una sola llamada: {len(titles)}")
        if titles:
            first = titles[0]
            print(f"  Campos: {sorted(first)}")
            sample = {k: first.get(k) for k in ("simbolo", "ultimoPrecio", "moneda", "fecha")}
            print(f"  Ejemplo: {sample}")
    elif isinstance(body, dict) and "activos" in body:
        # Datos personales: solo cantidad y nombres de campos, nunca montos.
        print(f"  Posiciones: {len(body['activos'])}")
        if body["activos"]:
            print(f"  Campos de cada posición: {sorted(body['activos'][0])}")
    elif isinstance(body, dict):
        print(f"  Campos: {sorted(body)}")
        print(f"  ultimoPrecio: {body.get('ultimoPrecio')} {body.get('moneda')}")


def main(env_path: Path = Path(".env"), transport: httpx2.BaseTransport | None = None) -> int:
    env = read_env(env_path)
    budget = CallBudget(MAX_CALLS)
    token = env.get("IOL_ACCESS_TOKEN", "")
    with httpx2.Client(base_url=BASE_URL, transport=transport, timeout=20) as client:

        def get(path: str) -> httpx2.Response:
            budget.spend()
            return client.get(path, headers={"Authorization": f"Bearer {token}"})

        quotes = get("/api/v2/Cotizaciones/acciones/argentina/Todos")
        if quotes.status_code == 401:
            budget.spend()
            renewed = client.post(
                "/token",
                data={"grant_type": "refresh_token", "refresh_token": env["IOL_REFRESH_TOKEN"]},
            )
            renewed.raise_for_status()
            tokens = renewed.json()
            token = tokens["access_token"]
            rotated = tokens.get("refresh_token", env["IOL_REFRESH_TOKEN"])
            write_env(env_path, {"IOL_ACCESS_TOKEN": token, "IOL_REFRESH_TOKEN": rotated})
            print(f"Token renovado (1 llamada). Campos: {sorted(tokens)}")
            print(f"  ¿IOL entregó un refresh token nuevo? {rotated != env['IOL_REFRESH_TOKEN']}")
            quotes = get("/api/v2/Cotizaciones/acciones/argentina/Todos")
        describe("Panel completo de acciones", quotes)
        describe("Cotización de GGAL", get("/api/v2/bCBA/Titulos/GGAL/Cotizacion"))
        describe("Portafolio", get("/api/v2/portafolio/argentina"))
    print(f"\nLlamadas usadas: {budget.used} de {MAX_CALLS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
