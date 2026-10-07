# API: arranque y base de datos del usuario

Cómo se arranca la API, dónde guarda sus datos y cómo evoluciona `user.sqlite`. Qué hace cada
endpoint está en la [API](../02-ddt/api.md); cómo se usa, en el
[manual de usuario](../04-manual-usuario/api.md).

## Arrancar

```bash
uv run uvicorn api.main:app --reload
```

- Sirve la API en `http://127.0.0.1:8000/api`, con la documentación interactiva en
  `http://127.0.0.1:8000/api/docs` y el contrato OpenAPI en `/api/openapi.json`.
- `--reload` reinicia el servidor al cambiar el código; es para desarrollo.

## Directorio de datos

| Variable | Por defecto | Qué es |
|----------|-------------|--------|
| `PTB_DATA_DIR` | `data` | Directorio con `reference.sqlite`, que escribe la [ingesta](ingesta.md), y `user.sqlite`, que escribe la API. |
| `PTB_WEB_DIR` | `web/dist` | Compilación de la web que la API sirve en `/` ([un solo proceso](web.md#un-solo-proceso)). Si no existe, solo se sirve la API. |

```bash
PTB_DATA_DIR=/ruta/a/otros-datos uv run uvicorn api.main:app
```

- **Sin `reference.sqlite`** la API arranca, pero los endpoints que necesitan los datos de
  referencia responden `503` con un mensaje que pide ejecutar la carga. Si la carga se hace con
  la API en marcha, la siguiente petición ya encuentra el fichero.
- **Con un `reference.sqlite` de una versión anterior**, al que le faltan tablas o columnas que
  necesita el código, esos endpoints responden también `503`, pidiendo repetir la carga y
  reiniciar la API.
- **Después de volver a cargar los datos**, hay que reiniciar la API: las conexiones abiertas
  siguen leyendo el fichero anterior ([ADR-0003](../03-adr/0003-dos-bases-de-datos-sqlite.md))
  y los datos de referencia de cada juego se guardan en memoria la primera vez que se usan
  ([contexto del motor](../02-ddt/modelo-datos.md#contexto-del-motor-gamecontext)).
  `GET /api/meta` dice con qué carga está trabajando.

## Base de datos del usuario (`user.sqlite`)

Guarda los favoritos, la configuración de las reglas, el *Hall of Fame* y las confirmaciones
de datos ([modelo de datos](../02-ddt/modelo-datos.md#base-de-datos-del-usuario-usersqlite)).
Es la única base de datos con datos que no se pueden regenerar: **haz copia de seguridad de
este fichero**.

### Migraciones

El esquema evoluciona con migraciones de [Alembic](https://alembic.sqlalchemy.org/), en
`db/user/migrations/versions/`.

- **Al arrancar**, la API crea `user.sqlite` si no existe y le aplica las migraciones
  pendientes. No hace falta ejecutar nada a mano.
- **A mano**, con la configuración de `db/user/alembic.ini`, que apunta a `data/user.sqlite`:

```bash
uv run alembic -c db/user/alembic.ini current              # revisión actual
uv run alembic -c db/user/alembic.ini upgrade head         # aplicar las pendientes
uv run alembic -c db/user/alembic.ini downgrade -1         # deshacer la última
```

### Crear una migración

Al cambiar un modelo de `db/user/models.py`:

1. Asegurarse de que `data/user.sqlite` está en la última revisión: arrancar la API una vez o
   ejecutar `upgrade head`.
2. Generar la migración, con un mensaje en inglés que describa el cambio:
   `uv run alembic -c db/user/alembic.ini revision --autogenerate -m "add favorite notes"`.
3. Revisar el fichero generado: Alembic no detecta todo (por ejemplo, renombrar una columna).
   Las migraciones se ejecutan en *batch mode*, porque SQLite no permite alterar la mayoría de
   restricciones.
4. Documentar el cambio en el [modelo de datos](../02-ddt/modelo-datos.md) en el mismo PR.

`tests/db/test_user_schema.py` falla si un modelo cambia sin su migración.

## Implementación

El código está en `api/`: su índice, en [`api/README.md`](https://github.com/AlbertoMercado/pokemon-team-builder/blob/main/api/README.md), y qué hace cada
módulo, en su *docstring*. Los modelos de `user.sqlite` y sus migraciones están en `db/user/`
([`db/README.md`](https://github.com/AlbertoMercado/pokemon-team-builder/blob/main/db/README.md)).
