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
- **Título**: Conventional Commit + key de Jira, por ejemplo `feat(accounts): crear cuenta [PF-14]`. Lo valida el CI (excepto `chore(deps)` de Dependabot).
- **Merge**: *squash merge* a `develop`, así el título del PR queda como commit. De `develop` a `main` se usa *merge commit* para conservar el historial del sprint.
- Completar el checklist de la plantilla (Definition of Done).
- PRs chicos: idealmente menos de 400 líneas cambiadas.

## Calidad local
```powershell
ruff check --fix . ; ruff format .
mypy src
lint-imports
pytest --cov
```
pre-commit ejecuta ruff y valida el mensaje de commit automáticamente.

## Versionado
SemVer con tags `vMAJOR.MINOR.PATCH` sobre `main`, al cierre de los sprints que generan release (ver [roadmap](docs/scrum/roadmap.md)).
