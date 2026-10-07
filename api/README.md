# api/

**Qué es**: la API HTTP con FastAPI: los routers validan la entrada, los servicios montan el
`GameContext` y llaman a `core/`, y los repositorios acceden a `db/`.

**Por qué existe**: expone los casos de uso a la web y a otras integraciones
([ADR-0002](../docs/03-adr/0002-monolito-modular-nucleo-puro.md)).

**Contenido** (el detalle, en el *docstring* de cada módulo):

| Ruta | Qué es |
|------|--------|
| `main.py` | `create_app(settings)` y `app`, la que sirve uvicorn. |
| `config.py` | `Settings`: directorio de datos (`PTB_DATA_DIR`) y de la web compilada (`PTB_WEB_DIR`). |
| `database.py` | Bases de datos: migra `user.sqlite` al arrancar y responde `503` si `reference.sqlite` falta o es de otra versión. |
| `dependencies.py` | Dependencias de los routers (sesiones, directorio de datos, juego de la ruta). |
| `errors.py` | Errores de los casos de uso y su código HTTP. |
| `web.py` | Sirve la web compilada en `/`. |
| `openapi.py` | Exporta el contrato OpenAPI sin arrancar la API. |
| `routers/` | Un router por grupo de endpoints. |
| `schemas/` | Modelos pydantic de peticiones y respuestas: el contrato OpenAPI. |
| `services/` | Casos de uso, uno por módulo (contexto, revisión, generación, *Hall of Fame*, catálogo, imágenes, enlaces a WikiDex…). |
| `repositories/` | Acceso a `db/`. |

**Más información**: convenciones y decisiones en el [DDT de la API](../docs/02-ddt/api.md);
cómo se arranca en [Operación](../docs/05-operacion/api.md); cómo se usa en el
[manual](../docs/04-manual-usuario/api.md); dependencias permitidas en la
[arquitectura](../docs/02-ddt/arquitectura.md#reglas-de-dependencia).
