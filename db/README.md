# db/

**Qué es**: la capa de persistencia, con modelos SQLModel.

**Por qué existe**: concentra en un solo paquete los modelos de las dos bases de datos SQLite
([ADR-0003](../docs/03-adr/0003-dos-bases-de-datos-sqlite.md)).

**Qué hace**: define las tablas de `reference.sqlite` (escrita solo por `ingest/`) y de
`user.sqlite` (escrita solo por `api/`, con migraciones). Tablas y columnas en el
[modelo de datos](../docs/02-ddt/modelo-datos.md).

**Restricciones**: no importa ningún otro paquete del proyecto (`lint-imports`).

Más detalle en [Estructura del código](../docs/02-ddt/estructura-codigo.md).
