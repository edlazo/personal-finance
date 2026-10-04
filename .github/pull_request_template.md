## Historia / Issue
Jira: [PF-___](https://<tu-sitio>.atlassian.net/browse/PF-___)

## ¿Qué cambia?
-

## ¿Cómo se prueba?
-

## Definition of Done
- [ ] El título del PR es un Conventional Commit con la key de Jira, por ejemplo `feat(accounts): crear cuenta [PF-14]`.
- [ ] CI en verde: ruff, mypy `--strict`, import-linter, tests con cobertura ≥ 85 %, `alembic check`.
- [ ] Sin `DeprecationWarning`.
- [ ] Tests unitarios de dominio + integración/e2e del endpoint.
- [ ] Migración de Alembic incluida, si cambia el esquema.
- [ ] OpenAPI documentado (summary, descripción, ejemplos).
- [ ] Se cumplen todos los criterios de aceptación de la historia.
- [ ] Sin secretos ni datos personales en el código o en los fixtures.
