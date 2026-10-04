# db/

**Qué es**: la capa de persistencia, con modelos SQLModel.

**Por qué existe**: concentra en un solo paquete los modelos de las dos bases de datos SQLite
([ADR-0003](../docs/03-adr/0003-dos-bases-de-datos-sqlite.md)).

**Qué hace**: define las tablas de `reference.sqlite` (escrita solo por `ingest/`) y de
`user.sqlite` (escrita solo por `api/`, con migraciones). Tablas y columnas en el
[modelo de datos](../docs/02-ddt/modelo-datos.md).

**Contenido**:

| Ruta | Qué hace |
|------|----------|
| `sqlite.py` | `create_sqlite_engine(path)`: motor de SQLite con las claves foráneas activadas. |
| `reference/` | Modelos de `reference.sqlite` y `create_reference_schema(engine)`. Uno por grupo de tablas: `games.py`, `pokemon.py`, `evolution.py`, `battles.py` y `meta.py`; `base.py` tiene la clase base, los enums y las restricciones comunes. |
| `user/` | Modelos y migraciones de `user.sqlite`. Pendiente. |

**Restricciones**: no importa ningún otro paquete del proyecto (`lint-imports`).

Más detalle en [Estructura del código](../docs/02-ddt/estructura-codigo.md) y en la
[implementación de reference.sqlite](../docs/02-ddt/modelo-datos.md#implementacion-de-referencesqlite).
