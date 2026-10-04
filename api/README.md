# api/

**Qué es**: la capa de aplicación HTTP con FastAPI, pendiente de implementar.

**Por qué existe**: expone los casos de uso al frontend ([API](../docs/02-ddt/api.md)).

**Qué hace**: los routers validan la entrada HTTP, los servicios montan el `GameContext` a
partir de las dos bases de datos y llaman a `core/`, y los repositorios acceden a `db/`.

**Restricciones**: puede importar `core/` y `db/`, nunca `ingest/` (`lint-imports`).

Más detalle en [Estructura del código](../docs/02-ddt/estructura-codigo.md).
