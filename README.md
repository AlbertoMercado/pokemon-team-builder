# pokemon-team-builder

Aplicación personal y sin ánimo de lucro que, a partir de una lista de Pokémon favoritos y un
juego objetivo, genera un equipo de 6 según reglas configurables (duras = filtros, blandas =
puntuación ponderada).

La aplicación está completa: catálogo y favoritos, reglas configurables, revisión de los datos
sin verificar, generación del equipo con sugerencias y el *Hall of Fame* con tu recorrido. Carga
los datos de las generaciones 1 a 3; de los juegos objetivo, Rojo Fuego y Verde Hoja tienen ya
todos sus datos curados (combates clave y mecánicas), y Rubí, Zafiro y Esmeralda están
pendientes. Qué contiene cada directorio:
[estructura del código](docs/02-ddt/estructura-codigo.md).

## Puesta en marcha

Requiere [uv](https://docs.astral.sh/uv/) y Node 24
([entorno de desarrollo](docs/05-operacion/entorno-desarrollo-macos.md)).

```bash
uv sync                                       # Python 3.13 y dependencias
uv run python -m ingest                       # carga los datos (data/reference.sqlite)
cd web && npm ci && npm run build && cd ..    # compila la web
uv run uvicorn api.main:app                   # la aplicación en http://127.0.0.1:8000
```

Cómo se usa: [manual de usuario](docs/04-manual-usuario/index.md). Para desarrollar:

```bash
uv run pre-commit install        # activa los hooks de calidad
uv run mkdocs serve              # documentación en local
```

Consulta [`CLAUDE.md`](CLAUDE.md) para el stack, la estructura y las convenciones, y
[`docs/`](docs/index.md) para la documentación completa.

## Licencia

[MIT](LICENSE). Pokémon y sus nombres son marcas de Nintendo, Creatures Inc. y GAME FREAK inc.;
este proyecto no está afiliado a ellos.
