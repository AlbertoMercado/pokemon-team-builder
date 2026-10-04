# Usar la API

La API es la interfaz HTTP de la aplicación: la usa la web y se puede usar directamente, por
ejemplo para probarla o automatizar algo. Qué hace cada endpoint, en detalle, está en la
[API](../02-ddt/api.md); cómo se arranca y se configura, en
[Operación](../05-operacion/api.md).

!!! note "Disponible por ahora"
    Arrancar la API, consultar su versión y la de los datos, gestionar los favoritos y las
    reglas y ver los juegos objetivo. La revisión de datos, la generación de equipos, el *Hall
    of Fame* y el catálogo se irán añadiendo a esta guía según se implementen
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

## Favoritos

Los equipos se generan siempre a partir de tu lista de favoritos, común a todos los juegos.
Añade la **evolución hasta la que quieres llegar**, con su forma: `butterfree`, no `caterpie`;
`vulpix-alola` para Vulpix de Alola.

```bash
curl -X PUT http://127.0.0.1:8000/api/favorites/dragonite      # añadir
curl http://127.0.0.1:8000/api/favorites                       # listar
curl -X DELETE http://127.0.0.1:8000/api/favorites/dragonite   # quitar
```

Añadir un favorito que ya tienes no cambia nada. Si la forma no existe en los datos cargados,
la respuesta es `404`. La lista dice cuántos tienes (`total`) y, de cada uno, su número, su
nombre y sus tipos actuales.

## Reglas

```bash
curl http://127.0.0.1:8000/api/rules
```

Devuelve las 20 reglas del catálogo con su descripción, su tipo, si están activas y, en las
blandas, su peso. Por defecto todas las configurables están activas.

```bash
# Desactivar una regla dura (por ejemplo, permitir tipos repetidos)
curl -X PATCH http://127.0.0.1:8000/api/rules/RN-12 \
     -H "Content-Type: application/json" -d '{"enabled": false}'

# Cambiar el peso de una regla blanda (de 0 a 10)
curl -X PATCH http://127.0.0.1:8000/api/rules/RN-17 \
     -H "Content-Type: application/json" -d '{"weight": 8}'
```

Las reglas estructurales, como «el equipo tiene 6 Pokémon» (RN-01), no se pueden desactivar:
la respuesta es `409` con el motivo. Tus cambios se guardan y se mantienen entre sesiones.

## Juegos objetivo

```bash
curl http://127.0.0.1:8000/api/games
```

Los juegos que puedes elegir para generar un equipo, en orden de lanzamiento. Solo aparecen los
que tienen datos cargados y permiten la crianza.

## Errores habituales

| Respuesta | Causa | Solución |
|-----------|-------|----------|
| `503` «No hay datos de referencia…» | No se han cargado los datos. | Ejecuta la [carga](cargar-datos.md); la siguiente petición ya los encuentra. |
| `404` al añadir un favorito | La forma no existe en los datos cargados. Hoy solo están las generaciones 1 a 3. | Revisa el identificador (en inglés y en minúsculas, como `mr-mime`). |
| `409` al cambiar una regla | La regla no se puede desactivar, o no es blanda y le has dado peso. | El mensaje dice cuál de las dos. |
| `Address already in use` al arrancar | Ya hay otra API (u otro programa) en el puerto 8000. | Para la otra o arranca en otro puerto: `--port 8001`. |
