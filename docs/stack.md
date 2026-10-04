# Stack tecnológico y arquitectura

> Estado verificado el **2026-10-02** (PyPI, GitHub, python.org). Ninguna dependencia está deprecada.
> Cualquier cambio de stack se propone en Refinement y queda registrado en este documento.

## 1. Runtime e infraestructura

| Tecnología | Versión | Justificación |
|---|---|---|
| Python | 3.14.8 | Última versión estable (2026-09-30). Tipado moderno y mejoras de performance. |
| PostgreSQL | 17 | Tipo `NUMERIC` exacto para dinero, transacciones ACID, índices parciales y JSONB. |
| Docker / Compose | 27.x | Mismo entorno en local, CI y producción. Postgres local sin instalar nada. |
| GitHub + Actions | — | Repo, CI/CD y registry (GHCR) en un solo lugar. |
| Jira Cloud | — | Gestión Scrum: backlog, sprints, burndown y velocity. |

## 2. Dependencias Python

Fuente de verdad: [`requirements.txt`](../requirements.txt) y [`requirements-dev.txt`](../requirements-dev.txt), con versiones fijadas con `==`.

### Runtime
| Paquete | Rol | Por qué este y no otro |
|---|---|---|
| fastapi[standard] | Framework API | Async, OpenAPI automático, integración nativa con Pydantic. `[standard]` trae fastapi-cli y uvicorn: se corre con `fastapi dev` / `fastapi run --workers N`. |
| pydantic / pydantic-settings | Validación, schemas y config | Estándar de FastAPI. La configuración es tipada desde variables de entorno. |
| email-validator | Validación de email | Requerido por `EmailStr` de Pydantic. |
| python-multipart | Form data / uploads | Login OAuth2 (form) e import de archivos Balanz. |
| sqlalchemy[asyncio] 2.1 | ORM | Estilo 2.x tipado (`Mapped[]`, `select()`), soporte async maduro. |
| asyncpg | Driver PostgreSQL | El driver async más rápido para Postgres. |
| alembic | Migraciones | Herramienta oficial de SQLAlchemy, con autogenerate y `alembic check` en CI. |
| pyjwt | JWT | Mantenido y simple. Reemplaza a python-jose, que no tiene mantenimiento. |
| pwdlib[argon2] | Hash de contraseñas | Argon2id. Reemplaza a passlib (sin mantenimiento), como recomienda FastAPI. |
| cryptography | Cifrado simétrico (Fernet) | Guarda cifradas las credenciales de IOL de cada usuario. |
| httpx | Cliente HTTP async | API sync/async y base del TestClient de FastAPI. Queda detrás de puertos. |
| tenacity | Reintentos | Backoff exponencial para las APIs externas inestables. |
| apscheduler 3.11 | Scheduler | Jobs en proceso (worker): cotizaciones, recurrentes, snapshots. Es la línea estable; la 4.x sigue en pre-release. |
| structlog | Logging | Logs JSON estructurados con contexto (request_id, user_id). |
| openpyxl | Lectura Excel | Import de movimientos exportados desde Balanz. |

### Desarrollo y calidad
| Paquete | Rol |
|---|---|
| ruff | Lint + formato (reemplaza flake8, isort y black). `--fix` en pre-commit y en CI. |
| mypy (`--strict`) | Tipado estático. |
| import-linter | Hace cumplir las reglas de capas hexagonales (por ejemplo, que `domain` no importe `infrastructure`). |
| pre-commit | Hooks locales: ruff fix/format y validación de commit-msg. |
| pytest, pytest-asyncio, pytest-cov | Tests async con cobertura mínima del 85%. |
| testcontainers[postgres] | PostgreSQL real y efímero en tests de integración. |
| respx | Mock de httpx para los adaptadores (dolarapi, IOL, etc.). |
| polyfactory | Fábricas de datos de prueba a partir de modelos Pydantic y dataclasses. |

### Descartados (deprecados o redundantes)
| Descartado | Motivo | Alternativa |
|---|---|---|
| gunicorn + `uvicorn.workers` | El worker está deprecado. `uvicorn-worker` está en Alpha y sin soporte declarado para 3.14. | `fastapi run --workers N` |
| Invocar `uvicorn` a mano | Innecesario | `fastapi dev` / `fastapi run` |
| passlib | Sin mantenimiento | pwdlib |
| python-jose | Sin mantenimiento | PyJWT |
| uv / poetry | Decisión del proyecto: solo pip + requirements | pip + venv |

### Patrones deprecados prohibidos
- `@app.on_event("startup")` → usar `lifespan`.
- SQLAlchemy 1.x (`session.query()`, `declarative_base()`) → `select()`, `DeclarativeBase`, `Mapped[]`.
- Pydantic v1 (`class Config`, `orm_mode`, `.dict()`) → `model_config`, `from_attributes`, `.model_dump()`.
- `datetime.utcnow()` → `datetime.now(UTC)`.
- `typing.List/Dict/Optional` → `list`, `dict`, `X | None`.

Esto se garantiza con `filterwarnings = ["error::DeprecationWarning"]` en pytest y con las reglas `UP` (pyupgrade) de ruff.

### Puntos a vigilar
- **httpx**: sin release desde 2024-12, pero el repo está activo. Si se discontinúa, se reemplaza el adaptador sin tocar el dominio.
- **openpyxl**: sin release desde 2024-06; es estable. Se reevalúa en el spike de import Balanz (Sprint 6).

## 3. Arquitectura: Hexagonal por módulos

```
           ┌──────────────── api (FastAPI routers, schemas) ────────────────┐
           │                                                                 │
HTTP ──▶   │   application (casos de uso, DTOs)  ──▶  domain (entidades,     │
           │                                           value objects, reglas,│
           │                                           puertos = Protocols)  │
           │                                                 ▲               │
           └─ infrastructure (SQLAlchemy repos, adaptadores HTTP) ┘          │
                         implementa los puertos del dominio
```

**Reglas de dependencia** (verificadas por import-linter):
1. `domain` no importa nada de FastAPI, SQLAlchemy, httpx ni de otras capas.
2. `application` depende solo de `domain`.
3. `infrastructure` y `api` dependen de `application` / `domain`, nunca al revés.
4. Un módulo usa a otro **solo a través de su capa `application`**, nunca de sus modelos ORM.

### Estructura
```
src/app/
├─ main.py            # create_app() + lifespan
├─ worker.py          # scheduler APScheduler
├─ config.py          # Settings
├─ shared/            # kernel: Money, Currency, RateType, errores, Clock, UnitOfWork, paginación
└─ modules/
   ├─ identity/       # usuarios, auth JWT, preferencias
   ├─ accounts/       # cuentas ARS/USD: ahorro, efectivo, billetera, broker, wallet cripto
   ├─ ledger/         # transacciones, categorías, transferencias
   ├─ fx/             # cotizaciones (MEP, oficial, blue, CCL, cripto)
   ├─ investments/    # instrumentos, trades, posiciones, precios
   ├─ credit_cards/   # tarjetas, resúmenes, cuotas
   ├─ debts/          # préstamos y deudas
   ├─ planning/       # recurrentes y presupuestos
   ├─ reports/        # patrimonio, flujo, categorías, evolución
   └─ assets/         # (futuro) bienes
   cada módulo/
   ├─ domain/  application/  infrastructure/  api/
```

## 4. Reglas de dinero
- Siempre `decimal.Decimal`, nunca `float`.
- Columnas: importes `NUMERIC(20,2)`; cantidades, precios y cotizaciones `NUMERIC(28,10)`.
- Value object `Money(amount, currency)`: operar con monedas distintas sin conversión explícita es un error de dominio.
- Monedas: `ARS`, `USD`. Tipos de cotización: `MEP` (default), `OFICIAL`, `BLUE`, `CCL`, `CRIPTO`.
- Los saldos se **derivan** de las transacciones; no se guardan saldos mutables.
- Bonos y ONs cotizan cada 100 VN.

## 5. Integraciones externas (puertos → adaptadores)
| Puerto | Adaptador | Fuente |
|---|---|---|
| `ExchangeRateProvider` | `DolarApiProvider` | dolarapi.com (oficial, blue, bolsa = MEP, CCL, cripto) |
| `PriceProvider` | `IolPriceProvider` | API de InvertirOnline (OAuth2 password grant) |
| `PriceProvider` | `Data912Provider` | data912 (respaldo para CEDEARs, bonos y ONs) |
| `PriceProvider` | `CoinGeckoProvider` | CoinGecko (cripto) |
| `PortfolioImporter` | `BalanzFileImporter` | CSV/Excel exportado de Balanz (no tiene API pública) |

Todos tienen fallback de **carga manual** y en los tests se reemplazan por fakes en memoria.

## 6. CI/CD
| Workflow | Disparador | Jobs |
|---|---|---|
| `pr-checks.yml` | PR a `develop`/`main` | Encadenados: `pr-rules` (1 commit, ≤ 400 líneas, nombre de rama; solo a `develop`) → `prefix` (lista permitida + `[PF-n]`) → `lint` (ruff check/format --check) → `typecheck`, `test`, `migrations` |
| `ci.yml` | push a `develop`/`main` | lint, mypy, import-linter, pytest + cobertura (Postgres service), `alembic check` |

El CI **no autocorrige**: el lint-fix se hace localmente con los hooks de pre-commit (pre-commit, commit-msg y pre-push), que bloquean el commit o el push y muestran el comando para corregir. El CI verifica que el código subido sea idéntico a la salida de ruff, usando la misma versión fijada. Detalle en [CONTRIBUTING.md](../CONTRIBUTING.md).
| `docker.yml` | push a `main` / tags `v*` | Build multi-stage y push a `ghcr.io` |
| Dependabot | Semanal | pip + GitHub Actions |
