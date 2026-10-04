# data/

**Qué es**: los datos de la aplicación, no código.

**Por qué existe**: separa los datos curados a mano, que se versionan, de los generados, que
no ([ADR-0005](../docs/03-adr/0005-datos-curados-yaml.md)).

**Qué contiene**:

| Ruta | Contenido | ¿En git? |
|------|-----------|----------|
| `curated/` | YAML curados a mano (combates clave, mecánicas de juego…), validados con pydantic por la ingesta. | Sí |
| `cache/` | Descargas de la ingesta: `pokeapi/<commit>/` (CSV) y `wikidex/` (páginas). Se pueden regenerar. | No |
| `*.sqlite` | `reference.sqlite` y `user.sqlite`. | No |

Más detalle en [Estructura del código](../docs/02-ddt/estructura-codigo.md).

**Ficheros curados**:

| Fichero | Qué contiene |
|---------|--------------|
| `curated/pokeapi.yaml` | Commit fijado del volcado CSV de PokeAPI ([ADR-0004](../docs/03-adr/0004-pokeapi-volcado-csv.md)). Cambiarlo es actualizar los datos. |
| `curated/games.yaml` | Mecánicas de cada juego objetivo (reloj, concursos) que condicionan las evoluciones. |
| `curated/breeding.yaml` | Bebés que solo nacen con incienso (Azurill, Wynaut). |
| `curated/arrival.yaml` | Regla con la que se propone qué Pokémon pueden llegar a cada juego objetivo. |
| `curated/key_battles/*.yaml` | Lista de combates clave de cada grupo de versiones y dónde está su equipo en WikiDex (página, sección y rótulo). |

Esquema, significado y cómo añadir un juego: [Datos curados](../docs/02-ddt/datos-curados.md).
