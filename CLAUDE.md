# CLAUDE.md

Guía para trabajar en este repositorio con Claude Code.

## Descripción del proyecto

**pokemon-team-builder** es una aplicación personal y sin ánimo de lucro. A partir de una lista
de Pokémon favoritos y un juego objetivo, genera un equipo de 6 según reglas configurables:

- **Reglas duras**: actúan como filtros; un candidato o equipo que no las cumple se descarta.
- **Reglas blandas**: puntuación ponderada; cada regla aporta una puntuación multiplicada por
  su peso configurable, y se elige el equipo con mayor puntuación total.

## Stack

| Capa | Tecnología |
|------|------------|
| Ingesta de datos | Python 3.13, httpx, mwparserfromhell, pydantic |
| Motor y API | FastAPI, SQLModel |
| Base de datos | SQLite |
| Frontend | React + Vite + TypeScript + Tailwind |
| Calidad (Python) | ruff, mypy (strict), import-linter, pytest, hypothesis, pre-commit, gitleaks |
| Calidad (web) | ESLint, Prettier, Vitest, Playwright |
| Documentación | MkDocs Material (docs-as-code en Markdown), diagramas Mermaid |
| Gestión de entorno | uv |

### Fuentes de datos

- **PokeAPI**: datos base (especies, tipos, evoluciones, movimientos, juegos). Se carga desde
  su **volcado CSV fijado a un commit**, no desde la API REST (ADR-0004).
- **WikiDex**: equipos de los combates clave, vía API MediaWiki. **Siempre con caché local y
  rate limit**; nunca hacer peticiones masivas sin caché. Identificarse con un `User-Agent`
  descriptivo.
- **Datos curados**: `data/curated/*.yaml`, versionados y validados con pydantic (ADR-0005).
- **Tests sin red**: `tests/conftest.py` hace fallar cualquier petición HTTP; los tests usan
  extractos reales guardados en `tests/<paquete>/fixtures/`.
- **Pokémon Showdown**: aplazado; ninguna regla lo necesita por ahora (ADR-0004).

## Estructura

```
docs/
  01-ddf/             Documento de Diseño Funcional (requisitos y reglas RN-XX)
  02-ddt/             Documento de Diseño Técnico
  03-adr/             Architecture Decision Records (0000-plantilla.md + NNNN-titulo.md)
  04-manual-usuario/  Manual de usuario
  05-operacion/       Instalación, despliegue, ingesta y mantenimiento
ingest/               Descarga, parseo y normalización de fuentes → reference.sqlite
core/                 Dominio puro: reglas RN-XX y motor de generación, sin I/O
db/                   Modelos SQLModel de reference.sqlite y user.sqlite (Alembic)
api/                  API FastAPI: routers → services → repositories, sobre core/ y db/
data/                 curated/*.yaml en git; cache/ y *.sqlite fuera de git
web/                  Frontend React + Vite + TypeScript + Tailwind
tests/                Tests de Python (pytest + hypothesis)
.github/workflows/    CI de GitHub Actions (ci.yml: Python, Documentación, Secretos)
```

`core/` debe mantenerse puro (sin acceso a red ni BD, solo biblioteca estándar) para poder
testearlo con hypothesis. Dependencias permitidas: `api → core, db` e `ingest → db`
([arquitectura](docs/02-ddt/arquitectura.md), ADR-0002). Se comprueban con los contratos de
`import-linter` de `pyproject.toml` y con `tests/test_architecture.py`.

Qué es, por qué existe y qué hace cada directorio: [estructura del código](docs/02-ddt/estructura-codigo.md).
Cada directorio de código tiene un `README.md` y cada paquete un *docstring* en su `__init__.py`.

## Convenciones

- **Idioma**: documentación, commits, issues y PR en **español**; código, identificadores,
  nombres de ficheros de código y comentarios técnicos en **inglés**.
- **Flujo de trabajo**: GitHub Flow. `main` está protegida; todo cambio entra por PR desde una
  rama `feat/`, `fix/`, `docs/`, `chore/` o `test/`.
- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/es/) en español,
  p. ej. `feat(core): añadir filtro por juego objetivo (RN-03)`.
- **Versionado**: SemVer. Mientras sea `0.x`, los cambios incompatibles suben la versión menor.
- **Decisiones de arquitectura**: toda decisión relevante se registra como ADR en
  `docs/03-adr/` a partir de `0000-plantilla.md`, con numeración correlativa.
- **Tipado**: mypy en modo `strict`; no usar `Any` ni `# type: ignore` sin justificar.
- **Documentación del código**: todo código o cambio de base de datos se documenta **en el
  mismo PR**: qué es, por qué existe y qué hace (docstring de módulo, `README.md` en
  directorios nuevos), tablas y migraciones en el [modelo de datos](docs/02-ddt/modelo-datos.md),
  y el DDT u Operación afectados. Si hace falta, se crea una página nueva y se enlaza en
  `mkdocs.yml`. Detalle en [estructura del código](docs/02-ddt/estructura-codigo.md#documentacion-del-codigo).

### Reglas de negocio (RN-XX)

**Toda regla de negocio se numera como `RN-XX` en el DDF (`docs/01-ddf/`) y se referencia en
tests e issues.**

- El DDF es la fuente de verdad: cada regla tiene un identificador `RN-XX` estable (no se
  reutilizan números de reglas eliminadas), su tipo (dura/blanda) y su descripción.
- Cada test que verifica una regla lleva el marcador `@pytest.mark.rn("RN-XX")` y menciona la
  regla en su nombre o docstring.
- Issues, PR y commits que implementan o modifican una regla citan su `RN-XX`.
- No implementar una regla de negocio que no esté documentada en el DDF: primero se documenta.
- Con el mismo criterio de identificadores estables, los requisitos funcionales se numeran
  `RF-XX` y las decisiones funcionales pendientes `CA-XX` (cuestiones abiertas del DDF).

## Comandos habituales

| Tarea | Comando | Estado |
|-------|---------|--------|
| Instalar dependencias | `uv sync` | ✅ |
| Lint | `uv run ruff check .` | ✅ |
| Formatear | `uv run ruff format .` | ✅ |
| Tipos | `uv run mypy` | ✅ |
| Contratos de dependencia | `uv run lint-imports` | ✅ |
| Tests | `uv run pytest` | ✅ |
| Hooks de pre-commit | `uv run pre-commit install` / `uv run pre-commit run --all-files` | ✅ |
| Documentación en local | `uv run mkdocs serve` | ✅ |
| Construir documentación | `uv run mkdocs build --strict` | ✅ |
| Ejecutar ingesta | `uv run python -m ingest [--data-dir DIR] [--offline]` ([detalle](docs/05-operacion/ingesta.md)) | ✅ Solo PokeAPI todavía |
| Arrancar API | `uv run uvicorn api.main:app --reload` | ⏳ Pendiente |
| Frontend en desarrollo | `cd web && npm run dev` | ⏳ Pendiente |
| Lint / formato web | `cd web && npm run lint` / `npm run format` | ⏳ Pendiente |
| Tests unitarios web | `cd web && npm run test` | ⏳ Pendiente |
| Tests E2E | `cd web && npm run test:e2e` | ⏳ Pendiente |

Actualiza esta tabla cuando un comando pendiente pase a existir.

### CI

`.github/workflows/ci.yml` se ejecuta en cada PR y en cada push a `main` con tres jobs:

- **Python**: pre-commit (sin gitleaks, mypy ni lint-imports), `mypy` con el entorno del
  proyecto, contratos de dependencia (`lint-imports`) y `pytest`.
- **Documentación**: `mkdocs build --strict`.
- **Secretos**: gitleaks sobre todo el historial.

Los tres son comprobaciones obligatorias para fusionar en `main`. Cuando exista `web/`, se añadirá
un job para el frontend.
