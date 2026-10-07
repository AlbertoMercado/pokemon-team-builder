# Estructura del código

Qué hay en cada directorio del repositorio y cómo se comprueba que las dependencias entre
paquetes respetan la [arquitectura](arquitectura.md#reglas-de-dependencia).

## Directorios

Cada directorio tiene un `README.md` con su índice y cada fichero, su *docstring* o comentario de
cabecera ([cómo se documenta](documentacion.md#el-readme-de-un-directorio)).

| Directorio | Qué es | Índice |
|------------|--------|--------|
| `core/` | Dominio puro: las reglas `RN-XX` y el motor de generación ([motor](motor.md)). | [`core/README.md`](https://github.com/AlbertoMercado/pokemon-team-builder/blob/main/core/README.md) |
| `db/` | Modelos SQLModel de `reference.sqlite` y `user.sqlite` y migraciones ([modelo de datos](modelo-datos.md)). | [`db/README.md`](https://github.com/AlbertoMercado/pokemon-team-builder/blob/main/db/README.md) |
| `ingest/` | CLI que carga los datos de referencia ([ingesta](../05-operacion/ingesta.md)). | [`ingest/README.md`](https://github.com/AlbertoMercado/pokemon-team-builder/blob/main/ingest/README.md) |
| `api/` | API HTTP con FastAPI ([API](api.md)). | [`api/README.md`](https://github.com/AlbertoMercado/pokemon-team-builder/blob/main/api/README.md) |
| `web/` | Frontend React ([web](../05-operacion/web.md)). | [`web/README.md`](https://github.com/AlbertoMercado/pokemon-team-builder/blob/main/web/README.md) |
| `data/` | Datos curados (en git) y generados (fuera de git) ([datos curados](datos-curados.md)). | [`data/README.md`](https://github.com/AlbertoMercado/pokemon-team-builder/blob/main/data/README.md) |
| `tests/` | Tests de Python ([estrategia de pruebas](arquitectura.md#estrategia-de-pruebas)). | [`tests/README.md`](https://github.com/AlbertoMercado/pokemon-team-builder/blob/main/tests/README.md) |
| `docs/` | Documentación MkDocs ([cómo se documenta](documentacion.md)); `docs/hooks/`, los *hooks* que la generan en parte. | [Inicio](../index.md) |
| `.claude/` | Skills de Claude Code del proyecto: [publicar una versión](../05-operacion/versiones.md#publicar-una-version). | — |

## Reglas de dependencia

Las dependencias permitidas entre paquetes están en la
[arquitectura](arquitectura.md#reglas-de-dependencia). Se comprueban de dos formas:

### Contratos de import-linter

[import-linter](https://import-linter.readthedocs.io/) analiza los `import` del código y
comprueba los contratos definidos en `pyproject.toml` (sección `[tool.importlinter]`):

| Contrato | Comprueba |
|----------|-----------|
| `core-pure` | `core/` no importa `db/`, `ingest/` ni `api/`. |
| `db-base` | `db/` no importa `core/`, `ingest/` ni `api/`. |
| `ingest-only-db` | `ingest/` no importa `core/` ni `api/`. |
| `api-not-ingest` | `api/` no importa `ingest/`. |

```bash
uv run lint-imports
```

Se ejecuta como hook de pre-commit (al hacer commit de ficheros `.py`) y como paso propio,
*Contratos de dependencia*, en el job de Python de la CI. Si un contrato se rompe, la salida
indica el módulo, el import y la línea, p. ej.:

```text
core no depende de ningún otro paquete del proyecto BROKEN
-   core.engine -> db (l.1)
```

### Guardián de pureza de `core/`

import-linter solo puede prohibir paquetes que se nombran uno a uno. Para garantizar que
`core/` usa **solo la biblioteca estándar**, sea cual sea la biblioteca que se intente usar,
`tests/test_architecture.py` recorre los ficheros de `core/` y falla si alguno importa un
módulo que no está en `sys.stdlib_module_names` ni es el propio `core`. Se ejecuta con el
resto de tests (`uv run pytest`).

## Hooks de pre-commit con el entorno del proyecto

`mypy` y `lint-imports` se ejecutan en pre-commit como hooks **locales** (`uv run …`), con el
entorno del proyecto, en lugar de con un entorno aislado de pre-commit. Así ven todas las
dependencias del código (SQLModel, pydantic…) sin mantener una segunda lista en
`.pre-commit-config.yaml`. En CI se ejecutan como pasos propios del job de Python.

## Añadir un paquete o una dependencia

- **Nuevo paquete de Python de primer nivel**: añadirlo a `root_packages` y a los contratos de
  `[tool.importlinter]`, a `files` de `[tool.mypy]`, a esta página, con su `README.md` y su *docstring*. Si cambia la arquitectura, con un ADR.
- **Nueva dependencia permitida entre paquetes**: es un cambio de arquitectura. Se registra en
  un ADR y se actualizan los contratos y la
  [arquitectura](arquitectura.md#reglas-de-dependencia).

## Documentación del código

Dónde se documenta cada cosa y qué se actualiza en cada PR: [cómo se documenta](documentacion.md).
