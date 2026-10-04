# data/

**Qué es**: los datos de la aplicación, no código.

**Por qué existe**: separa los datos curados a mano, que se versionan, de los generados, que
no ([ADR-0005](../docs/03-adr/0005-datos-curados-yaml.md)).

**Qué contiene**:

| Ruta | Contenido | ¿En git? |
|------|-----------|----------|
| `curated/` | YAML curados a mano (combates clave, mecánicas de juego…), validados con pydantic por la ingesta. | Sí |
| `cache/` | Respuestas descargadas por la ingesta. Se pueden regenerar. | No |
| `*.sqlite` | `reference.sqlite` y `user.sqlite`. | No |

Más detalle en [Estructura del código](../docs/02-ddt/estructura-codigo.md).
