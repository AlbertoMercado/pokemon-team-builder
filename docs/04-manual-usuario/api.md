# Usar la API

La API es la interfaz HTTP de la aplicación: la usa la web y se puede usar directamente, por
ejemplo para probarla o automatizar algo. Qué hace cada endpoint, en detalle, está en la
[API](../02-ddt/api.md); cómo se arranca y se configura, en
[Operación](../05-operacion/api.md).

!!! note "Disponible por ahora"
    Arrancar la API y consultar su versión y la de los datos (`GET /api/meta`). Los
    favoritos, las reglas, la revisión de datos, la generación de equipos, el *Hall of Fame* y
    el catálogo se irán añadiendo a esta guía según se implementen
    ([plan de la API](../02-ddt/plan-api.md#fases)).

## Antes de empezar

- Haber cargado los datos al menos una vez ([cargar los datos](cargar-datos.md)). Sin ellos,
  la API arranca, pero casi todo responde `503`.
- Estar en el directorio del proyecto, con las dependencias instaladas (`uv sync`).

## Arrancar la API

```bash
uv run uvicorn api.main:app --reload
```

Cuando aparezca `Application startup complete`, la API está en `http://127.0.0.1:8000/api`.
Para pararla, `Ctrl+C`.

La primera vez crea `data/user.sqlite`, donde guarda tus favoritos, tus reglas, tu *Hall of
Fame* y lo que confirmes. **Haz copia de seguridad de ese fichero**: es lo único que no se puede
volver a generar.

## Probarla desde el navegador

Abre `http://127.0.0.1:8000/api/docs`: es la documentación interactiva. Cada endpoint tiene un
botón **Try it out** para llamarlo y ver la respuesta.

## Comprobar con qué datos trabaja

```bash
curl http://127.0.0.1:8000/api/meta
```

```json
{
  "app_version": "0.1.0",
  "data": {
    "pokeapi_commit": "bc92d3b…",
    "ingested_at": "2026-10-04T09:25:10Z",
    "games": ["red", "blue", "yellow", "gold", "silver", "crystal", "ruby", "sapphire", "emerald", "firered", "leafgreen"]
  }
}
```

- `app_version`: la versión de la aplicación.
- `data`: la carga de datos con la que trabaja: el commit de PokeAPI (aquí abreviado; la API
  devuelve los 40 caracteres), cuándo terminó y qué juegos tiene.

Si has vuelto a cargar los datos y `ingested_at` sigue siendo la fecha anterior, reinicia la
API.

## Errores habituales

| Respuesta | Causa | Solución |
|-----------|-------|----------|
| `503` «No hay datos de referencia…» | No se han cargado los datos. | Ejecuta la [carga](cargar-datos.md); la siguiente petición ya los encuentra. |
| `Address already in use` al arrancar | Ya hay otra API (u otro programa) en el puerto 8000. | Para la otra o arranca en otro puerto: `--port 8001`. |
