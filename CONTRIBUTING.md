# Guía de contribución

## Ramas
| Rama | Propósito | Protección |
|---|---|---|
| `main` | Producción. Cada merge publica la imagen Docker en GHCR. | Solo recibe PRs desde `develop`; CI en verde y 1 aprobación. Sin push directo ni force-push. |
| `develop` | Integración del sprint en curso. | PR obligatorio, CI en verde. Sin push directo ni force-push. |
| `feature/PF-<n>-<slug>` | Una historia o tarea de Jira. | Sale de `develop` y vuelve por PR. |
| `fix/PF-<n>-<slug>` | Corrección de bug. | Igual que feature. |
| `hotfix/PF-<n>-<slug>` | Bug urgente en producción. | Sale de `main`; PR a `main` y back-merge a `develop`. |

Ejemplo: `feature/PF-14-crear-cuenta`.

## Commits: Conventional Commits
```
<tipo>(<scope opcional>): <descripción en imperativo, minúscula>

[cuerpo opcional]

[footer opcional: Refs: PF-14 | BREAKING CHANGE: ...]
```
| Tipo | Uso |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `refactor` | Cambio interno sin alterar el comportamiento |
| `test` | Tests nuevos o modificados |
| `docs` | Documentación |
| `style` | Formato (sin cambio de lógica) |
| `perf` | Mejora de performance |
| `build` | Dependencias, Docker, empaquetado |
| `ci` | Pipelines |
| `chore` | Mantenimiento general |

Scopes sugeridos: `identity`, `accounts`, `ledger`, `fx`, `investments`, `credit-cards`, `debts`, `planning`, `reports`, `shared`, `deps`.

Ejemplos:
- `feat(accounts): permitir crear cuentas en USD`
- `fix(fx): usar cotización de venta para convertir ARS a USD`

## Pull Requests
- **Título**: Conventional Commit + key de Jira, por ejemplo `feat(accounts): crear cuenta [PF-14]`.
- **Merge**: *squash merge* a `develop`. De `develop` a `main` se usa *merge commit* para conservar el historial del sprint.
- Completar el checklist de la plantilla (Definition of Done).

### Validaciones automáticas del PR (workflow `pr-checks`)
Se ejecutan en este orden. Si una falla, las siguientes no corren.

| # | Check | Regla | Aplica a |
|---|---|---|---|
| 1 | `pr-rules / single-commit` | El PR tiene **exactamente 1 commit nuevo** (no cuentan los commits de un PR apilado anterior que ya entró a `develop`; el tamaño también se mide solo sobre el commit nuevo). Para corregir, se hace `git commit --amend` y luego `git push --force-with-lease`. | PRs a `develop` |
| 2 | `pr-rules / size` | **additions + deletions ≤ 400**. No cuentan `migrations/versions/**`, `docs/**`, `requirements*.txt`, `frontend/package-lock.json` ni `frontend/src/components/ui/**` (componentes generados por shadcn). | PRs a `develop` |
| 3 | `pr-rules / branch-name` | La rama respeta `feature|fix|hotfix|chore/PF-<n>-<slug>`. Dependabot está exento. | PRs a `develop` |
| — | `pr-rules / origin` | A `main` solo llegan PRs desde `develop` o `hotfix/*`. | PRs a `main` |
| 4 | `prefix` | El prefijo del **título del PR y de cada commit** está en la lista permitida (ver abajo), el título incluye `[PF-<n>]` y ninguno pasa de 72 caracteres. Dependabot está exento de la key y del largo; en los PRs a `main` el largo de los commits no se valida, porque GitHub les suma ` (#n)` al hacer squash. | Todos |
| 5 | `lint` | `ruff check` + `ruff format --check` sin cambios: el código subido tiene que ser idéntico a lo que produciría el linter (misma versión de ruff fijada en `requirements-dev.txt`). | Todos |
| 6 | `typecheck`, `test`, `migrations` | mypy, import-linter, pytest con cobertura ≥ 85 % (Postgres como service), `alembic upgrade head` + `alembic check`. | Todos |
| 7 | `image` | Construye la imagen Docker sin publicarla y verifica que la API y el worker importan adentro. La publicación es solo desde `main` (`docker.yml`). | Todos |

Los checks 5 a 7 viven en el workflow reutilizable `quality.yml`, que también corre en cada push a `develop` y `main` (`ci.yml`). El prefijo se valida con [`scripts/check_commit_msg.py`](scripts/check_commit_msg.py), el mismo script del hook `commit-msg`.

**Prefijos permitidos:** `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `style`, `build`, `ci`, `chore`, `revert`.

Los PRs de release (`develop` → `main`) traen todos los commits del sprint, así que están exentos de los checks 1 a 3.

## Calidad local (hooks de git)
El CI **no corrige** el código: solo verifica. La corrección se hace en tu máquina, y los hooks de pre-commit **bloquean** el commit si algo no está bien:

| Hook | Momento | Qué hace si falla |
|---|---|---|
| `ruff check` + `ruff format --check` | `pre-commit` | Bloquea el commit y muestra el comando para corregir |
| Validación de prefijo | `commit-msg` | Bloquea el commit si el prefijo no está en la lista |
| `mypy` + `pytest -x -q` (tests unitarios) | `pre-push` | Bloquea el push |

Para corregir el lint:
```powershell
ruff check --fix . ; ruff format .
git add -A ; git commit --amend --no-edit
```
Instalación de los hooks (una sola vez): `pre-commit install` (instala los tres tipos). Los hooks usan las herramientas del venv, así que hay que commitear y pushear con el venv activado.

### Tests de integración sin Docker
Los tests de integración levantan Postgres con testcontainers. Si Docker no anda, sirve cualquier Postgres 16 o 17 apuntado con `TEST_DATABASE_URL`, por ejemplo los binarios que trae el wheel `pgserver` (se descarga con `pip download pgserver --no-deps --only-binary :all: --python-version 3.12 --platform win_amd64` y se descomprime):

```bash
pg/pgserver/pginstall/bin/initdb -D pgdata -U postgres -A trust
pg/pgserver/pginstall/bin/pg_ctl -D pgdata -o "-p 54329" -l pg.log start
pg/pgserver/pginstall/bin/createdb -h 127.0.0.1 -p 54329 -U postgres personal_finance_test
TEST_DATABASE_URL=postgresql+asyncpg://postgres@127.0.0.1:54329/personal_finance_test pytest --cov
```

En Windows, `postgres` no arranca con un usuario administrador: hay que usar `pg_ctl`.

## Versionado
SemVer con tags `vMAJOR.MINOR.PATCH` sobre `main`, al cierre de los sprints que generan release (ver [roadmap](docs/scrum/roadmap.md)).

Cada push a `main` publica `ghcr.io/edlazo/personal-finance:latest` y `:sha-<corto>`; cada tag `vX.Y.Z` publica `:vX.Y.Z` (workflow `docker.yml`).

Dependabot abre PRs semanales a `develop` (pip, npm y GitHub Actions) con título `build(deps): ...`. Si uno queda desactualizado o en conflicto, no uses "Update branch" ni el editor de conflictos de GitHub: comentá `@dependabot rebase` (o `@dependabot recreate` si alguien tocó la rama).
