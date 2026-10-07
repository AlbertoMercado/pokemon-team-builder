# data/

**Qué es**: los datos de la aplicación, no código.

**Por qué existe**: separa los datos curados a mano, que se versionan, de los generados, que
no ([ADR-0005](../docs/03-adr/0005-datos-curados-yaml.md)).

**Contenido**:

| Ruta | Qué es | ¿En git? |
|------|--------|----------|
| `curated/` | Datos curados a mano en YAML, validados por la ingesta. | Sí |
| `cache/` | Descargas de la ingesta (CSV de PokeAPI, páginas de WikiDex, imágenes y portadas). Se pueden regenerar. | No |
| `*.sqlite` | `reference.sqlite` (lo construye la ingesta) y `user.sqlite` (los datos del usuario). | No |
| `reports/` | Informes de las cargas bloqueadas, cuando estén implementadas (#78). | No |

**Más información**: qué contiene cada fichero curado, su esquema y cómo añadir un juego en
[datos curados](../docs/02-ddt/datos-curados.md); la caché en
[ingesta de datos](../docs/05-operacion/ingesta.md#primera-ejecucion-y-cache).
