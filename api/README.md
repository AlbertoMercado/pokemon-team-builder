# api/

**Qué es**: la capa de aplicación HTTP con FastAPI. Implementadas las fases 1 a 3
del [plan](../docs/02-ddt/plan-api.md): arranque, configuración, metadatos, favoritos, reglas,
juegos, construcción del `GameContext` y revisión de los datos sin verificar.

**Por qué existe**: expone los casos de uso al frontend ([API](../docs/02-ddt/api.md)).

**Qué hace**: los routers validan la entrada HTTP, los servicios montan el `GameContext` a
partir de las dos bases de datos y llaman a `core/`, y los repositorios acceden a `db/`.

**Contenido**:

| Ruta | Qué hace |
|------|----------|
| `main.py` | `create_app(settings)` y `app`, la que sirve uvicorn. |
| `config.py` | `Settings`: el directorio de datos (`PTB_DATA_DIR`). |
| `database.py` | Motores y sesiones de las dos bases de datos; `503` si falta `reference.sqlite`. |
| `errors.py` | Errores de los casos de uso y su código HTTP (`404`, `409`, `422`). |
| `dependencies.py` | Dependencias de los routers: sesiones de las bases de datos y datos de referencia del juego de la ruta (`404` si no es juego objetivo). |
| `routers/` | Un router por grupo de endpoints de la [API](../docs/02-ddt/api.md). |
| `services/` | Casos de uso. `context.py` construye el `GameContext` (con la parte de referencia de cada juego en caché) y `review.py`, la revisión de datos. |
| `repositories/` | Acceso a `db/`. |
| `schemas/` | Modelos pydantic de las peticiones y respuestas (el contrato OpenAPI). |

Cómo se arranca: [Operación](../docs/05-operacion/api.md).

**Restricciones**: puede importar `core/` y `db/`, nunca `ingest/` (`lint-imports`).

Más detalle en [Estructura del código](../docs/02-ddt/estructura-codigo.md).
