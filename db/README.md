# db/

**Qué es**: la capa de persistencia: los modelos SQLModel de las dos bases de datos SQLite.

**Por qué existe**: concentra en un solo paquete los modelos de `reference.sqlite` y
`user.sqlite` ([ADR-0003](../docs/03-adr/0003-dos-bases-de-datos-sqlite.md)).

**Contenido** (el detalle, en el *docstring* de cada módulo):

| Ruta | Qué es |
|------|--------|
| `sqlite.py` | Motor de SQLite con las claves foráneas activadas. |
| `reference/` | Modelos de `reference.sqlite`, uno por grupo de tablas, y su esquema. |
| `user/` | Modelos de `user.sqlite`, el *hash* de los valores propuestos y las migraciones de Alembic. |

**Más información**: tablas, columnas y migraciones en el
[modelo de datos](../docs/02-ddt/modelo-datos.md); crear una migración en
[Operación](../docs/05-operacion/api.md#crear-una-migracion); dependencias permitidas en la
[arquitectura](../docs/02-ddt/arquitectura.md#reglas-de-dependencia).
