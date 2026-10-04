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
| 1 | `pr-rules / single-commit` | El PR tiene **exactamente 1 commit**. Para corregir, se hace `git commit --amend` y luego `git push --force-with-lease`. | PRs a `develop` |
| 2 | `pr-rules / size` | **additions + deletions ≤ 400**. No cuentan `migrations/versions/**`, `docs/**` ni `requirements*.txt`. | PRs a `develop` |
| 3 | `pr-rules / branch-name` | La rama respeta `feature|fix|hotfix|chore/PF-<n>-<slug>`. | PRs a `develop` |
| 4 | `prefix` | El prefijo del **título del PR y de cada commit** está en la lista permitida (ver abajo) y el título incluye `[PF-<n>]`. Dependabot está exento de la key. | Todos |
| 5 | `lint` | `ruff check` + `ruff format --check` sin cambios: el código subido tiene que ser idéntico a lo que produciría el linter (misma versión de ruff fijada en `requirements-dev.txt`). | Todos |
| 6 | `typecheck`, `test`, `migrations` | mypy, import-linter, pytest con cobertura, `alembic check`. | Todos |

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
Instalación de los hooks (una sola vez): `pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push`.

## Versionado
SemVer con tags `vMAJOR.MINOR.PATCH` sobre `main`, al cierre de los sprints que generan release (ver [roadmap](docs/scrum/roadmap.md)).
