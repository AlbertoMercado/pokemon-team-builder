# api/

**Qué es**: la capa de aplicación HTTP con FastAPI. Implementadas las fases 1 a 6
del [plan](../docs/02-ddt/plan-api.md): arranque, configuración, metadatos, catálogo, favoritos,
reglas, juegos, construcción del `GameContext`, revisión de los datos sin verificar, generación
de equipos y *Hall of Fame* con el recorrido.

**Por qué existe**: expone los casos de uso al frontend ([API](../docs/02-ddt/api.md)).

**Qué hace**: los routers validan la entrada HTTP, los servicios montan el `GameContext` a
partir de las dos bases de datos y llaman a `core/`, y los repositorios acceden a `db/`.

**Contenido**:

| Ruta | Qué hace |
|------|----------|
| `main.py` | `create_app(settings)` y `app`, la que sirve uvicorn. |
| `config.py` | `Settings`: el directorio de datos (`PTB_DATA_DIR`). |
| `database.py` | Motores y sesiones de las dos bases de datos; `503` si falta `reference.sqlite`. |
| `openapi.py` | `python -m api.openapi [FICHERO]`: exporta el OpenAPI sin arrancar la API, para generar el cliente de la web. |
| `errors.py` | Errores de los casos de uso y su código HTTP (`404`, `409`, `422`). |
| `dependencies.py` | Dependencias de los routers: sesiones de las bases de datos, directorio de datos y datos de referencia del juego de la ruta (`404` si no es juego objetivo). |
| `routers/` | Un router por grupo de endpoints de la [API](../docs/02-ddt/api.md). |
| `services/` | Casos de uso. `context.py` construye el `GameContext` (con la parte de referencia de cada juego en caché), `review.py` revisa los datos, `generation.py` genera los equipos y comprueba el equipo elegido en el resultado, `hall_of_fame.py` gestiona el recorrido (RN-16), `catalog.py` busca Pokémon y monta su ficha, `images.py` da la URL y el fichero de la imagen de cada forma y de la portada de cada juego (ADR-0010, ADR-0011), `wikidex.py` construye los enlaces a las fuentes en WikiDex y `rounding.py` redondea las puntuaciones con el método del mayor resto (CA-51). |
| `repositories/` | Acceso a `db/`. |
| `schemas/` | Modelos pydantic de las peticiones y respuestas (el contrato OpenAPI). |

Cómo se arranca: [Operación](../docs/05-operacion/api.md).

**Restricciones**: puede importar `core/` y `db/`, nunca `ingest/` (`lint-imports`).

Más detalle en [Estructura del código](../docs/02-ddt/estructura-codigo.md).
