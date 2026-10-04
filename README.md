# pokemon-team-builder

Aplicación personal y sin ánimo de lucro que, a partir de una lista de Pokémon favoritos y un
juego objetivo, genera un equipo de 6 según reglas configurables (duras = filtros, blandas =
puntuación ponderada).

> Proyecto en fase inicial: existe la estructura de paquetes, pero todavía no hay lógica de
> aplicación. Qué contiene cada directorio: [estructura del código](docs/02-ddt/estructura-codigo.md).

## Puesta en marcha

```bash
uv sync                          # instala Python 3.13 y dependencias de desarrollo
uv run pre-commit install        # activa los hooks de calidad
uv run mkdocs serve              # documentación en http://127.0.0.1:8000
```

Consulta [`CLAUDE.md`](CLAUDE.md) para el stack, la estructura y las convenciones, y
[`docs/`](docs/index.md) para la documentación completa.

## Licencia

[MIT](LICENSE). Pokémon y sus nombres son marcas de Nintendo, Creatures Inc. y GAME FREAK inc.;
este proyecto no está afiliado a ellos.
