# Usar la API

La API es la interfaz HTTP de la aplicación: la usa la web y se puede usar directamente, por
ejemplo para probarla o automatizar algo. Esta guía explica cómo hacer cada tarea; todos los
endpoints, sus parámetros y los campos de cada respuesta están en la
[referencia de la API](../02-ddt/api-referencia.md), y cómo se arranca y se configura, en
[Operación](../05-operacion/api.md). Lo mismo se puede hacer desde la [web](web.md).

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
  "app_version": "1.2.0",
  "data": {
    "pokeapi_commit": "bc92d3b…",
    "sprites_commit": "8491ffd…",
    "ingested_at": "2026-10-04T09:25:10Z",
    "games": ["red", "blue", "yellow", "gold", "silver", "crystal", "ruby", "sapphire", "emerald", "firered", "leafgreen"]
  }
}
```

Dice la versión de la aplicación y la carga de datos con la que trabaja (los commits aparecen
aquí abreviados; qué es cada campo, en la
[referencia](../02-ddt/api-referencia.md#esquema-meta)).

Si has vuelto a cargar los datos y `ingested_at` sigue siendo la fecha anterior, reinicia la
API.

## Buscar Pokémon

```bash
curl "http://127.0.0.1:8000/api/pokemon?q=vulpix"            # por nombre
curl "http://127.0.0.1:8000/api/pokemon?type=dragon"          # por tipo
curl "http://127.0.0.1:8000/api/pokemon?favorite=true"        # solo tus favoritos
curl http://127.0.0.1:8000/api/pokemon/haunter                # ficha
```

- La lista tiene todos los Pokémon cargados en orden de la Pokédex Nacional, con sus tipos
  actuales y si están en tus favoritos (`favorite`). Los filtros se pueden combinar.
- La búsqueda no distingue mayúsculas ni tildes y también mira el identificador, que es el que
  usan el resto de endpoints: busca «mr mime» y verás que es `mr-mime`.
- Las formas regionales son entradas propias, con su región: `vulpix` y `vulpix-alola`.
- La **ficha** muestra además la línea evolutiva completa (`line`), con la etapa de cada forma,
  y cómo se evoluciona (`evolutions`): el disparador (`level-up`, `use-item`, `trade`…) y sus
  condiciones (`minimum_level`, `trigger_item`…), en los términos de PokeAPI. Si hay varios
  métodos, cualquiera sirve.
- Los tipos son los **actuales**. Para generar equipos se usan los que tenía en el juego
  objetivo.
- Cada Pokémon trae en `image_url` la dirección de su imagen, o `null` si no la tiene, y la
  ficha además `artwork_url`, la de su ilustración oficial. Las formas regionales tienen las
  suyas. Puedes abrirla en el navegador o descargarla:

```bash
curl -o vulpix.png http://127.0.0.1:8000/api/pokemon/vulpix-alola/image
```

  Las imágenes son de Nintendo, Creatures, GAME FREAK y The Pokémon Company; la carga de datos
  las descarga del repositorio de PokeAPI a tu ordenador y la API las sirve desde ahí.

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

Con `?all=true` aparecen todos los juegos cargados, también los que no pueden ser juego objetivo
(como Rojo u Oro), que sí se pueden registrar en el [Hall of Fame](#hall-of-fame-tu-recorrido).
`target` dice si cada uno puede ser juego objetivo.

Cada juego trae en `cover_url` la dirección de su portada, o `null` si no la tiene, y en
`cover_source_url` la página de esa portada en WikiDex. Los registros del Hall of Fame traen las
mismas dos. Puedes abrirla en el navegador o descargarla:

```bash
curl -o rojo-fuego.png http://127.0.0.1:8000/api/games/firered/cover
```

Las portadas son de Nintendo, Creatures, GAME FREAK y The Pokémon Company. WikiDex las declara de
uso legítimo solo en sus artículos, así que son **solo para tu uso privado**: no las publiques ni
las compartas. La carga de datos las descarga a tu ordenador y la API las sirve desde ahí; si no
las quieres, carga los datos con `--no-covers` ([cargar datos](cargar-datos.md)).

## Revisar los datos de un juego

Algunos datos no se pueden cargar con certeza: la carga los deja **inferidos** (con una
propuesta) o **pendientes** (sin ella). Antes de generar un equipo tienes que confirmar los que
intervienen con tus favoritos y tus reglas ([RN-18](../01-ddf/reglas-negocio.md#rn-18)). Por
ejemplo, en Rojo Fuego: si el juego tiene ciclo de día y noche o concursos, y si cada favorito
puede llegar al juego y evolucionar antes de completarlo.

```bash
curl http://127.0.0.1:8000/api/games/firered/review
```

`pending` dice cuántos faltan; con 0 ya se puede generar. Cada dato de `facts` trae su clave
(`fact_key`), qué es (`name`), lo que propone la carga (`proposal`) y su estado (`status`):
`pending` o `confirmed`. No aparecen los favoritos que ya están descartados por otros motivos
(Zapdos no se puede criar, así que no importa si puede llegar).

```bash
# Aceptar de una vez todas las propuestas
curl -X POST http://127.0.0.1:8000/api/games/firered/review/accept-proposals

# Confirmar o corregir un dato: true o false…
curl -X PUT http://127.0.0.1:8000/api/games/firered/review/pokemon:firered:raichu:arrival \
     -H "Content-Type: application/json" -d '{"value": false}'

# …o, en un combate clave, la lista de Pokémon de su equipo
curl -X PUT http://127.0.0.1:8000/api/games/firered/review/battle:firered:misty \
     -H "Content-Type: application/json" -d '{"value": ["staryu", "starmie"]}'
```

- Aceptar las propuestas no rellena los datos **pendientes**: no tienen propuesta, así que los
  tienes que confirmar uno a uno.
- Lo que confirmas se usa tal cual. Si confirmas un dato erróneo, el equipo puede no ser el
  adecuado.
- Tus confirmaciones se guardan. Si una carga nueva propone otro valor para alguno, vuelve a
  aparecer como `pending` con `outdated` a `true`.
- Los datos que la carga obtuvo sin ambigüedad (automáticos) no aparecen y no se pueden
  cambiar.
- En un combate clave, `source_url` enlaza a la versión de la página de WikiDex de la que sale
  su equipo, para que puedas comprobarlo antes de confirmarlo.

## Generar un equipo

Con tus favoritos y los datos del juego confirmados:

```bash
curl -X POST http://127.0.0.1:8000/api/games/firered/generations
```

Si queda algún dato por confirmar, la respuesta es `409` y `detail.pending` dice cuáles son:
confírmalos ([revisar los datos](#revisar-los-datos-de-un-juego)) y vuelve a generar.

Qué mirar en la respuesta:

- **`status`**: `complete` si hay un equipo de 6 favoritos. Si es `incomplete`,
  `incomplete_reason` dice por qué: una regla de presencia necesita un Pokémon que no tienes
  en favoritos (`reserved_slot`), tienes menos de 6 favoritos válidos
  (`not_enough_candidates`) o no hay 6 que cumplan juntos las reglas (`no_valid_team`).
- **`groups`**: los equipos recomendados. Si varios empatan, aparecen todos; los que solo se
  diferencian en Pokémon con los mismos tipos se agrupan, y `positions` dice qué Pokémon
  puede ocupar cada puesto (por ejemplo, Cloyster o Lapras).
- **`breakdown`** de cada equipo: lo que aporta cada regla blanda a la puntuación, que suma el
  total. `score` es lo bien que el equipo cumple la regla, en porcentaje. Si una regla pesa
  mucho y no te convence, cambia su peso en [reglas](#reglas) y vuelve a generar.
- **`open_slots`**: si el equipo tiene menos de 6, los huecos y los Pokémon que encajan en
  ellos, de mejor a peor. Los que tienen `verified` a `false` dependen de datos que no has
  confirmado. Si te gusta alguno, añádelo a favoritos y vuelve a generar. Con varios huecos
  libres, cada sugerencia encaja con el equipo, pero dos sugerencias pueden no encajar entre sí.
- **`discards`**: los favoritos que no han podido entrar y por qué (por ejemplo, Zapdos no se
  puede criar).
- **`confirmed_facts`**: los datos que confirmaste y que se han usado.

Las puntuaciones son números enteros redondeados. Dos equipos con la misma cifra no tienen por
qué estar empatados: el orden se decide con los valores exactos. El resultado no se guarda;
generar otra vez con lo mismo da el mismo resultado.

## Comprobar un equipo elegido

Antes de registrar un equipo formado con los del resultado (una alternativa de cada posición y
una sugerencia para cada hueco), puedes comprobar que cumple tus reglas. Es lo que hace el
selector de la web:

```bash
curl -X POST http://127.0.0.1:8000/api/games/firered/team-checks \
  -H 'Content-Type: application/json' \
  -d '{"members": ["gengar", "dragonite", "lapras", "vaporeon"]}'
```

- **`valid`**: si cumple las reglas activas.
- **`problems`**: cada regla que no cumple, con los miembros afectados y la explicación. Por
  ejemplo, dos sugerencias para huecos libres que comparten tipo (RN-12), o un equipo sin la
  evolución de Eevee que pide RN-14.
- **`unverified`**: los miembros con datos que no has confirmado. No es un problema.

No se guarda nada. Como al generar, responde `409` si queda algún dato por confirmar, y `422`
si repites un Pokémon o uno no existe en la generación del juego.

## Hall of Fame: tu recorrido

Cuando completes un juego, registra el equipo con el que lo hiciste. Los registros forman tu
**recorrido**, y al generar un equipo se excluyen las líneas evolutivas que ya usaste
([RN-16](../01-ddf/reglas-negocio.md#rn-16)): las del último juego completado y las de los
juegos de la misma generación que el que vas a jugar. La línea de Dragonite nunca se excluye y,
de la de Eevee, solo la evolución que usaste.

```bash
# Registrar un equipo (las notas son opcionales)
curl -X POST http://127.0.0.1:8000/api/hall-of-fame \
     -H "Content-Type: application/json" \
     -d '{"game": "leafgreen", "completed_on": "2026-05-01", "members": ["dragonite", "vaporeon", "gengar"]}'

curl http://127.0.0.1:8000/api/hall-of-fame                  # todo el recorrido
curl "http://127.0.0.1:8000/api/hall-of-fame?game=leafgreen"   # solo un juego

# Corregir un registro (por ejemplo, la fecha) o eliminarlo
curl -X PATCH http://127.0.0.1:8000/api/hall-of-fame/1 \
     -H "Content-Type: application/json" -d '{"completed_on": "2026-05-03"}'
curl -X DELETE http://127.0.0.1:8000/api/hall-of-fame/1
```

- Puedes registrar cualquier juego cargado, aunque no se pueda elegir como juego objetivo
  (por ejemplo, Rojo o Oro).
- El equipo tiene de 1 a 6 Pokémon. Usa la forma concreta: `vulpix-alola` para Vulpix de Alola.
- Se guardan los tipos que tenía cada Pokémon **en ese juego** (Magneton era solo Eléctrico en
  Rojo).
- El recorrido se ordena por fecha y, si dos coinciden, por el orden en que los registraste.
  `last` marca el último juego completado. Si te equivocas de fecha, corrígela: cambia qué se
  excluye.
- Si un Pokémon queda descartado por el recorrido, la generación lo dice en `discards`, con el
  motivo `journey` y el juego en que lo usaste. Para no aplicar esta regla, desactiva RN-16 en
  [reglas](#reglas).

## Errores habituales

| Respuesta | Causa | Solución |
|-----------|-------|----------|
| `404` al pedir una imagen | Esa forma no tiene imagen: la carga no pudo descargarla, o se ha borrado la caché. | Repite la [carga](cargar-datos.md) con conexión; el informe dice qué formas no tienen imagen. |
| `404` al pedir una portada | Ese juego no tiene portada: se cargó con `--no-covers`, WikiDex no la dio o se ha borrado la caché. | Repite la [carga](cargar-datos.md) con conexión y sin `--no-covers`; el informe dice qué juegos no tienen portada. |
| `503` «No hay datos de referencia…» | No se han cargado los datos. | Ejecuta la [carga](cargar-datos.md); la siguiente petición ya los encuentra. |
| `503` «Los datos de referencia son de una versión anterior…» | Has actualizado la aplicación y la nueva versión necesita datos que la carga anterior no tiene. | Repite la [carga](cargar-datos.md) y reinicia la API. |
| `404` al consultar una ficha | La forma no existe en los datos cargados. | Búscala en la lista (`?q=`) para ver su identificador. |
| `404` al añadir un favorito | La forma no existe en los datos cargados. Hoy solo están las generaciones 1 a 3. | Revisa el identificador (en inglés y en minúsculas, como `mr-mime`). |
| `409` al cambiar una regla | La regla no se puede desactivar, o no es blanda y le has dado peso. | El mensaje dice cuál de las dos. |
| `404` al revisar un juego | El juego no es juego objetivo, o el dato no es de ese juego. | Consulta los juegos con `GET /api/games` y las claves con `GET …/review`. |
| `409` al confirmar un dato | El dato se cargó sin ambigüedad (automático): no se revisa. | Nada. |
| `422` al registrar en el *Hall of Fame* | El juego o algún Pokémon no existen en los datos cargados, o el Pokémon no existía en la generación de ese juego (Treecko en Rojo). El equipo tiene que tener de 1 a 6. | Revisa los identificadores y el juego. |
| `409` al generar | Quedan datos sin confirmar. | Confírmalos con la revisión; `detail.pending` dice cuáles. |
| `422` al confirmar un dato | El valor no es del tipo del dato (un booleano, o una lista en un combate clave) o el equipo incluye Pokémon que no existen en la generación del juego. | Revisa el valor y los identificadores. |
| `Address already in use` al arrancar | Ya hay otra API (u otro programa) en el puerto 8000. | Para la otra o arranca en otro puerto: `--port 8001`. |
