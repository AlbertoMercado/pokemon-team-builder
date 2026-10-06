# ingest/

**Qué es**: la CLI de carga de datos (`uv run python -m ingest`).

**Por qué existe**: los datos de referencia vienen de fuentes externas y se cargan de forma
puntual, no en cada arranque (RF-11).

**Qué hace**: extrae PokeAPI (volcado CSV e imágenes de los Pokémon), WikiDex (con caché y
límite de peticiones) y los datos curados, los valida y normaliza, y construye `reference.sqlite` en un fichero temporal
que solo sustituye al anterior si todo es correcto, también que las claves que usa
`user.sqlite` siguen existiendo.

**Contenido**:

| Ruta | Qué hace |
|------|----------|
| `__main__.py` | Punto de entrada de `python -m ingest`. |
| `cli.py` | Opciones (`--data-dir`, `--offline`) y fuentes de una carga completa. |
| `scope.py` | Alcance de la carga: generaciones y juegos que se cargan (CA-11). |
| `checks.py` | Comprobaciones de la primera carga: cantidades y casos conocidos. |
| `load.py` | `build_reference`: fichero temporal, filas, imágenes, comprobaciones, registro en `ingest_run` y sustitución atómica. |
| `user_keys.py` | Comprueba que lo que usa `user.sqlite` (favoritos, *Hall of Fame*, confirmaciones) sigue existiendo en la nueva carga (ADR-0003). |
| `report.py` | Informe de la carga: filas por tabla, datos por origen, avisos y errores. |
| `sources/` | Interfaz `Source` de las fuentes. |
| `sources/curated/` | Datos curados: esquemas de los YAML (`schemas.py`), lectura (`read_curated`) y la fuente de mecánicas y combates clave. |
| `sources/pokeapi/` | Fuente de PokeAPI: descarga con caché (`download.py`), imágenes de las formas con caché, recortadas o reducidas con Pillow (`sprites.py`, ADR-0010), validación de cada fila (`rows.py`), transformación (`transform.py`) e índice de Pokémon por nombre (`index.py`). |
| `sources/wikidex/` | Fuente de WikiDex: descarga con caché y límite de peticiones (`fetch.py`), portadas de los juegos con caché y reducidas con Pillow (`covers.py`, ADR-0011), procesado de las plantillas `{{Equipo}}` (`parse.py`) y filas de los combates clave. |

Fases del [plan de carga](../docs/02-ddt/plan-carga-datos.md).

**Restricciones**: solo puede importar `db/` (`lint-imports`).

Uso e informe en [Ingesta de datos](../docs/05-operacion/ingesta.md). Más detalle en
[Estructura del código](../docs/02-ddt/estructura-codigo.md).
