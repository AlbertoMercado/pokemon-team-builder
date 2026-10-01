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
| Calidad (Python) | ruff, mypy (strict), pytest, hypothesis, pre-commit, gitleaks |
| Calidad (web) | ESLint, Prettier, Vitest, Playwright |
| Documentación | MkDocs Material (docs-as-code en Markdown), diagramas Mermaid |
| Gestión de entorno | uv |

### Fuentes de datos

- **PokeAPI**: datos base (especies, tipos, estadísticas, movimientos, juegos).
- **Pokémon Showdown**: datos de combate (learnsets, formatos, habilidades).
- **WikiDex**: vía API MediaWiki. **Siempre con caché local y rate limit**; nunca hacer
  peticiones masivas sin caché. Identificarse con un `User-Agent` descriptivo.

## Estructura

```
docs/
  01-ddf/             Documento de Diseño Funcional (requisitos y reglas RN-XX)
  02-ddt/             Documento de Diseño Técnico
  03-adr/             Architecture Decision Records (0000-plantilla.md + NNNN-titulo.md)
  04-manual-usuario/  Manual de usuario
  05-operacion/       Instalación, despliegue, ingesta y mantenimiento
ingest/               Descarga, parseo y normalización de fuentes → SQLite
core/                 Motor de generación de equipos (filtros + puntuación), sin I/O
api/                  API FastAPI sobre el motor y la BD
web/                  Frontend React + Vite + TypeScript + Tailwind
tests/                Tests de Python (pytest + hypothesis)
.github/workflows/    CI de GitHub Actions
```

`core/` debe mantenerse puro (sin acceso a red ni BD) para poder testearlo con hypothesis.

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

### Reglas de negocio (RN-XX)

**Toda regla de negocio se numera como `RN-XX` en el DDF (`docs/01-ddf/`) y se referencia en
tests e issues.**

- El DDF es la fuente de verdad: cada regla tiene un identificador `RN-XX` estable (no se
  reutilizan números de reglas eliminadas), su tipo (dura/blanda) y su descripción.
- Cada test que verifica una regla lleva el marcador `@pytest.mark.rn("RN-XX")` y menciona la
  regla en su nombre o docstring.
- Issues, PR y commits que implementan o modifican una regla citan su `RN-XX`.
- No implementar una regla de negocio que no esté documentada en el DDF: primero se documenta.

## Comandos habituales

| Tarea | Comando | Estado |
|-------|---------|--------|
| Instalar dependencias | `uv sync` | ✅ |
| Lint | `uv run ruff check .` | ✅ |
| Formatear | `uv run ruff format .` | ✅ |
| Tipos | `uv run mypy` | ✅ |
| Tests | `uv run pytest` | ✅ |
| Hooks de pre-commit | `uv run pre-commit install` / `uv run pre-commit run --all-files` | ✅ |
| Documentación en local | `uv run mkdocs serve` | ✅ |
| Construir documentación | `uv run mkdocs build --strict` | ✅ |
| Ejecutar ingesta | `uv run python -m ingest ...` | ⏳ Pendiente |
| Arrancar API | `uv run uvicorn api.main:app --reload` | ⏳ Pendiente |
| Frontend en desarrollo | `cd web && npm run dev` | ⏳ Pendiente |
| Lint / formato web | `cd web && npm run lint` / `npm run format` | ⏳ Pendiente |
| Tests unitarios web | `cd web && npm run test` | ⏳ Pendiente |
| Tests E2E | `cd web && npm run test:e2e` | ⏳ Pendiente |

Mientras no haya ficheros `.py`, `mypy` termina con «There are no .py[i] files» y `pytest` con
código 5 («no tests ran»); es el comportamiento esperado.

Actualiza esta tabla cuando un comando pendiente pase a existir.
