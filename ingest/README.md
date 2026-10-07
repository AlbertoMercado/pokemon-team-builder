# ingest/

**Qué es**: la CLI de carga de datos (`uv run python -m ingest`), que construye
`reference.sqlite` a partir de PokeAPI, WikiDex y los datos curados.

**Por qué existe**: los datos de referencia vienen de fuentes externas y se cargan de forma
puntual, no en cada arranque ([RF-11](../docs/01-ddf/requisitos-funcionales.md#rf-11)).

**Contenido** (el detalle, en el *docstring* de cada módulo):

| Ruta | Qué es |
|------|--------|
| `__main__.py`, `cli.py` | Punto de entrada y opciones de la línea de comandos. |
| `scope.py` | Alcance de la carga: generaciones y juegos. |
| `load.py` | `build_reference`: construye la base de datos aparte y solo sustituye la anterior si todo es correcto. |
| `checks.py` | Comprobaciones de la carga: cantidades y casos conocidos. |
| `user_keys.py` | Que siga existiendo lo que usa `user.sqlite`. |
| `report.py` | Informe de la carga. |
| `sources/` | `Source`, la interfaz de una fuente. |
| `sources/pokeapi/` | PokeAPI: CSV del commit fijado, validación de filas, transformación e imágenes de los Pokémon. |
| `sources/wikidex/` | WikiDex: páginas de los combates clave y portadas de los juegos, con caché y límite de peticiones. |
| `sources/curated/` | Datos curados: esquemas y lectura de `data/curated/*.yaml`. |

**Más información**: cómo funciona, opciones e informe en
[ingesta de datos](../docs/05-operacion/ingesta.md); cómo se usa en el
[manual](../docs/04-manual-usuario/cargar-datos.md); dependencias permitidas en la
[arquitectura](../docs/02-ddt/arquitectura.md#reglas-de-dependencia).
