# Comandos y CI

Los comandos de desarrollo del proyecto y lo que comprueba la CI. Se ejecutan desde la raíz del
repositorio salvo los marcados «en `web/`». Cómo preparar el entorno la primera vez:
[entorno de desarrollo](entorno-desarrollo-macos.md).

## Python y datos

| Tarea | Comando | Detalle |
|-------|---------|---------|
| Instalar dependencias | `uv sync` | [Dependencias](dependencias.md) |
| Lint / formatear | `uv run ruff check .` / `uv run ruff format .` | |
| Tipos (mypy estricto) | `uv run mypy` | |
| Contratos de dependencia | `uv run lint-imports` | [Reglas de dependencia](../02-ddt/estructura-codigo.md#reglas-de-dependencia) |
| Tests | `uv run pytest` | [`tests/README.md`](https://github.com/AlbertoMercado/pokemon-team-builder/blob/main/tests/README.md) |
| Hooks de pre-commit | `uv run pre-commit install` / `uv run pre-commit run --all-files` | [Hooks](../02-ddt/estructura-codigo.md#hooks-de-pre-commit-con-el-entorno-del-proyecto) |
| Cargar los datos | `uv run python -m ingest [--data-dir DIR] [--offline] [--no-covers]` | [Ingesta](ingesta.md) |
| Ver la base de datos | `uvx datasette data/reference.sqlite` | [Consultar los datos](ingesta.md#consultar-los-datos) |
| Arrancar la aplicación | `uv run uvicorn api.main:app --reload` | [Arrancar la API](api.md) |
| Migrar `user.sqlite` (la API lo hace al arrancar) | `uv run alembic -c db/user/alembic.ini upgrade head` | [Migraciones](api.md#migraciones) |
| Documentación en local / construirla | `uv run mkdocs serve` / `uv run mkdocs build --strict` | [Cómo se documenta](../02-ddt/documentacion.md) |
| Dependencias desactualizadas | `uv tree --outdated --depth 1` | [Dependencias](dependencias.md) |

## Web (en `web/`)

| Tarea | Comando | Detalle |
|-------|---------|---------|
| Instalar dependencias | `npm ci` | [Web](web.md#instalar) |
| Desarrollo (con la API arrancada) | `npm run dev` | [Arrancar en desarrollo](web.md#arrancar-en-desarrollo) |
| Regenerar el cliente de la API (al cambiar la API, en el mismo PR) | `npm run api:generate` | [Cliente de la API](web.md#cliente-de-la-api) |
| Lint (ESLint estricto con tipos) | `npm run lint` | |
| Formatear / comprobar el formato (Prettier) | `npm run format` / `npm run format:check` | |
| Tipos | `npm run typecheck` | |
| Tests unitarios y de pantallas (Vitest) | `npm run test` (`npm run test:watch` mientras se trabaja) | [Pruebas de la web](web.md#pruebas) |
| Pruebas de extremo a extremo (Playwright) | `npm run test:e2e` (una vez antes: `npx playwright install chromium`) | [Extremo a extremo](web.md#pruebas-de-extremo-a-extremo) |
| Compilar en `web/dist` (la sirve la API en `/`) | `npm run build` | [Un solo proceso](web.md#un-solo-proceso) |
| Dependencias desactualizadas | `npm outdated` | [Dependencias](dependencias.md) |

## Versiones

Publicar una versión se le pide a Claude, con la skill `publicar-version`:
[publicar una versión](versiones.md#publicar-una-version).

## CI

`.github/workflows/ci.yml` se ejecuta en cada PR y en cada push a `main`. Sus cinco jobs son
comprobaciones obligatorias para fusionar en `main` (protección de la rama en GitHub):

| Job | Qué hace |
|-----|----------|
| **Python** | pre-commit (sin gitleaks, mypy ni lint-imports), `mypy` con el entorno del proyecto, `lint-imports` y `pytest`. |
| **Documentación** | `mkdocs build --strict`. |
| **Web** | `npm ci`; regenera el cliente y falla si `schema.d.ts` cambia; lint, formato, tipos, tests y compilación. |
| **E2E** | Instala Python, Node y Chromium y ejecuta `npm run test:e2e`. Si falla, sube el informe de Playwright como artefacto. |
| **Secretos** | gitleaks sobre todo el historial. |
