# API

API HTTP de la aplicación, servida por FastAPI bajo el prefijo `/api`. El contrato completo se
publica como OpenAPI en `/api/openapi.json`, del que se genera el cliente del frontend
([ADR-0007](../03-adr/0007-cliente-generado-openapi.md)), y la documentación interactiva en
`/api/docs`. Los endpoints marcados con ✅ están implementados; el resto llega con las fases
del [plan de la API](plan-api.md#fases). Cómo se arranca: [Operación](../05-operacion/api.md).

## Convenciones

- JSON en peticiones y respuestas, con nombres de campo en `snake_case`.
- Los recursos se identifican con las claves naturales del
  [modelo de datos](modelo-datos.md) (`firered`, `vulpix-alola`, `RN-07`).
- Los errores usan el formato por defecto de FastAPI (`{"detail": ...}`) con estos códigos.
  `detail` es un texto, salvo en los `422` de validación de FastAPI (una lista) y en el `409`
  de la generación, que es un objeto con el mensaje y los datos pendientes:
    - `404`: el recurso no existe.
    - `409`: la operación no se puede hacer en el estado actual (p. ej., generar con datos sin
      confirmar).
    - `422`: datos de entrada no válidos.
    - `503`: todavía no se han cargado los datos de referencia (`reference.sqlite`).
- Sin autenticación: la aplicación es de un solo usuario.

## Endpoints

### Catálogo

| Método | Ruta | Descripción | Requisitos |
|--------|------|-------------|------------|
| `GET` | `/api/pokemon` | Lista de Pokémon con su número total (`total`). Filtros: `q` (nombre), `type`, `favorite`. ✅ | RF-01 |
| `GET` | `/api/pokemon/{pokemon}` | Ficha: número, nombre, tipos actuales, línea evolutiva y método de cada evolución. `404` si la forma no existe. ✅ | RF-01, RF-02 |

- **Lista**: todas las formas cargadas, en orden de la Pokédex Nacional, cada una con su
  número, su nombre, sus tipos actuales, su región si es una forma regional y si está en
  favoritos. Las formas regionales son entradas propias
  ([RN-05](../01-ddf/reglas-negocio.md#rn-05)): `vulpix` y `vulpix-alola`, «Vulpix de Alola».
- **Filtros**, combinables: `q` busca una parte del nombre o del identificador sin distinguir
  mayúsculas ni tildes, y con los guiones del identificador como espacios (`mr mime`,
  `flabebe`); `type` deja los que tienen ese tipo actual; `favorite=true` o `false`, los que
  están o no en favoritos.
- **Ficha**: lo mismo que la lista y, además, la generación en que apareció la especie, si es
  legendaria o singular, la **línea evolutiva completa** (`line`, todas las formas de la cadena
  evolutiva con su etapa, ramas incluidas) y cada **evolución** (`evolutions`) con su mecanismo:

```json
{
  "pokemon": "haunter", "name": "Haunter", "dex_number": 93, "types": ["ghost", "poison"],
  "region": null, "favorite": false, "generation": 1, "species": "haunter",
  "is_legendary": false, "is_mythical": false,
  "line": [
    {"pokemon": "gastly", "name": "Gastly", "dex_number": 92, "types": ["ghost", "poison"], "region": null, "favorite": false, "stage": 1},
    {"pokemon": "haunter", "…": "…", "stage": 2},
    {"pokemon": "gengar", "…": "…", "stage": 3}
  ],
  "evolutions": [
    {"from_pokemon": "gastly", "to_pokemon": "haunter", "version_group": "firered-leafgreen",
     "methods": [{"trigger": "level-up", "conditions": {"minimum_level": 25}}]},
    {"from_pokemon": "haunter", "to_pokemon": "gengar", "version_group": "firered-leafgreen",
     "methods": [{"trigger": "trade", "conditions": {}}]}
  ]
}
```

El mecanismo es el disparador (`trigger`) y las condiciones (`conditions`) de PokeAPI, tal como
los guarda la ingesta ([modelo de datos](modelo-datos.md#evoluciones)); varias entradas en
`methods` son métodos alternativos. Como el método puede cambiar entre juegos, se muestra el
del grupo de versiones más reciente cargado que tiene esa evolución (`version_group`). La
interfaz traduce el disparador y las condiciones a texto.

### Favoritos

| Método | Ruta | Descripción | Requisitos |
|--------|------|-------------|------------|
| `GET` | `/api/favorites` | Lista de favoritos con su número total (`total`), en orden de la Pokédex Nacional. Cada uno con su forma, nombre, número, tipos actuales y cuándo se añadió. ✅ | RF-04 |
| `PUT` | `/api/favorites/{pokemon}` | Añade un favorito y lo devuelve. Es idempotente. `404` si la forma no existe en los datos cargados. ✅ | RF-03 |
| `DELETE` | `/api/favorites/{pokemon}` | Quita un favorito: `204`, o `404` si no lo era. ✅ | RF-03, RF-04 |

Los **tipos actuales** son los de la última generación cargada (hoy, la 3.ª: Clefairy es
Normal). Para generar se usan los del juego objetivo ([RN-10](../01-ddf/reglas-negocio.md#rn-10)).

### Reglas

| Método | Ruta | Descripción | Requisitos |
|--------|------|-------------|------------|
| `GET` | `/api/rules` | Las 20 reglas del catálogo, en orden, con su nombre, descripción, tipo (`hard`, `presence`, `soft` o `mechanism`), si son configurables, si están activas, su peso y su peso por defecto. ✅ | RF-06, RF-07 |
| `PATCH` | `/api/rules/{rule_id}` | Cambia `enabled`, `weight` (0 a 10) o los dos, y devuelve la regla. `404` si no existe; `409` si no es configurable o se da peso a una regla que no es blanda; `422` si el peso está fuera de rango o no se indica nada. ✅ | RF-06, RF-07 |

`user.sqlite` solo guarda las reglas que el usuario ha cambiado; el resto usa los valores por
defecto del catálogo ([CA-41](../01-ddf/cuestiones-abiertas.md#resueltas)).

### Juegos y revisión de datos

| Método | Ruta | Descripción | Requisitos |
|--------|------|-------------|------------|
| `GET` | `/api/games` | Juegos que pueden ser juego objetivo: los marcados como objetivo y con crianza, en orden de lanzamiento. ✅ | RF-05 |
| `GET` | `/api/games/{game}/review` | Datos inferidos o pendientes que intervienen en la generación, con su propuesta y su estado, y cuántos faltan por confirmar. `404` si el juego no es juego objetivo. ✅ | RF-15 |
| `PUT` | `/api/games/{game}/review/{fact_key}` | Confirma un dato con el valor propuesto o corregido (`{"value": ...}`): un booleano, o la lista de Pokémon del equipo si es un combate clave. Devuelve el dato. `404` si el dato no existe en el juego; `409` si es automático; `422` si el valor no es del tipo del dato o el equipo tiene Pokémon que no existen en la generación del juego. ✅ | RF-15 |
| `POST` | `/api/games/{game}/review/accept-proposals` | Acepta de una vez las propuestas inferidas que intervienen y aún no están confirmadas, y devuelve la revisión. Los datos pendientes, sin propuesta, se siguen tratando uno a uno. ✅ | RF-15 |

Qué datos intervienen lo decide `core.review.involved_facts`
([motor](motor.md#revision-de-datos-corereviewpy)): las mecánicas del juego, sus combates clave
si [RN-17](../01-ddf/reglas-negocio.md#rn-17) está activa y la existencia y la llegada de cada
favorito que no esté ya descartado con datos conocidos. De ellos, la revisión muestra los que
la carga dejó **inferidos** o **pendientes**; los automáticos no se revisan. Ejemplo con Raichu
de favorito en Rojo Fuego, tras confirmar su llegada:

```json
{
  "game": "firered",
  "pending": 2,
  "facts": [
    {
      "fact_key": "mechanic:firered:contests",
      "kind": "mechanic",
      "subject": "contests",
      "name": "Concursos",
      "origin": "inferred",
      "proposal": false,
      "status": "pending",
      "value": null,
      "confirmed_at": null,
      "outdated": false
    },
    {"fact_key": "mechanic:firered:day_night_cycle", "...": "..."},
    {
      "fact_key": "pokemon:firered:raichu:arrival",
      "kind": "arrival",
      "subject": "raichu",
      "name": "Raichu",
      "origin": "inferred",
      "proposal": false,
      "status": "confirmed",
      "value": false,
      "confirmed_at": "2026-10-04T20:15:02Z",
      "outdated": false
    }
  ]
}
```

| Campo | Qué es |
|-------|--------|
| `pending` | Datos con `status` `pending`. Con 0 se puede generar. |
| `kind` | `mechanic`, `key_battle`, `exists` (la forma se puede tener en el juego) o `arrival` (puede llegar y evolucionar antes de completarlo, [RN-03](../01-ddf/reglas-negocio.md#rn-03)). |
| `subject`, `name` | La mecánica, el combate clave o la forma, y su nombre en español (el del entrenador en un combate). |
| `origin` | Origen en la carga: `inferred` (con propuesta) o `pending` (sin ella). |
| `proposal`, `value` | Lo que propone la carga y lo que confirmó el usuario: booleanos o, en un combate clave, la lista de Pokémon de su equipo en orden. |
| `status` | `confirmed` si hay una confirmación para la propuesta actual; si no, `pending`. |
| `outdated` | Había una confirmación, pero una carga posterior propone otro valor: se vuelve a pedir ([RN-18](../01-ddf/reglas-negocio.md#rn-18)). |

Los datos salen en el orden en que se piden: primero los del juego (mecánicas, combates clave)
y después los de cada favorito en orden de la Pokédex Nacional, la existencia antes que la
llegada. Una confirmación guarda el hash de la propuesta a la que respondió
([modelo de datos](modelo-datos.md#implementacion-de-usersqlite)), así que una corrección del
usuario se mantiene mientras la carga proponga lo mismo. Se puede confirmar cualquier dato
revisable del juego, intervenga o no ahora: si después se añade el favorito, ya está
confirmado.

### Generación

| Método | Ruta | Descripción | Requisitos |
|--------|------|-------------|------------|
| `POST` | `/api/games/{game}/generations` | Genera los equipos con los favoritos, las reglas y las confirmaciones actuales. `409` con la lista de datos pendientes si queda alguno sin confirmar; `404` si el juego no es juego objetivo. ✅ | RF-08, RF-09, RF-10 |
| `POST` | `/api/games/{game}/team-checks` | Comprueba un equipo elegido en el selector del resultado (`{"members": [...]}`, de 1 a 6 formas) contra las reglas activas: `{"valid": ..., "problems": [...]}`. `409` si quedan datos sin confirmar. ⏳ Fase 6 del [plan de la web](plan-web.md#comprobacion-del-equipo). | RF-12, CA-53 |

La generación no se guarda: es un cálculo sin estado, y con los mismos datos da siempre la misma
respuesta. Ejemplo con los favoritos del escenario de Rojo Fuego, abreviado:

```json
{
  "game": "firered",
  "status": "complete",
  "incomplete_reason": null,
  "score": 19,
  "groups": [
    {
      "positions": [
        [{"pokemon": "magneton", "name": "Magneton", "dex_number": 82, "types": ["electric", "steel"]}],
        [
          {"pokemon": "cloyster", "name": "Cloyster", "dex_number": 91, "types": ["water", "ice"]},
          {"pokemon": "lapras", "name": "Lapras", "dex_number": 131, "types": ["water", "ice"]}
        ],
        "…"
      ],
      "teams": [
        {
          "members": ["magneton", "cloyster", "exeggutor", "rhydon", "flareon", "dragonite"],
          "score": 19,
          "dual_type_members": 5,
          "breakdown": [
            {"rule_id": "RN-06", "name": "Penalizar varias formas de la misma especie", "weight": 1, "score": 100, "contribution": 1, "penalized": []},
            {"rule_id": "RN-15", "name": "Penalizar evoluciones tediosas", "weight": 3, "score": 100, "contribution": 3, "penalized": []},
            {"rule_id": "RN-17", "name": "Tipos eficaces frente a los combates clave", "weight": 10, "score": 96, "contribution": 10, "penalized": []},
            {"rule_id": "RN-20", "name": "Penalizar las evoluciones aleatorias", "weight": 5, "score": 100, "contribution": 5, "penalized": []}
          ],
          "open_slots": []
        },
        "…"
      ]
    }
  ],
  "discards": [
    {"pokemon": "zapdos", "name": "Zapdos", "rule_id": "RN-11", "reason": "breeding", "detail": "Zapdos no se puede criar (grupos huevo de su línea: no-eggs)", "fact_key": null}
  ],
  "presence": [
    {"rule_id": "RN-13", "level": 1, "status": "candidates", "options": ["dragonite"], "detail": "…"},
    {"rule_id": "RN-14", "level": 1, "status": "candidates", "options": ["vaporeon", "jolteon", "flareon"], "detail": "…"}
  ],
  "confirmed_facts": [
    {"fact_key": "pokemon:firered:dragonite:arrival", "kind": "arrival", "name": "Dragonite", "value": true}
  ],
  "data_version": {"pokeapi_commit": "…", "ingested_at": "…", "games": ["…"]}
}
```

| Campo | Qué es |
|-------|--------|
| `status`, `incomplete_reason` | `complete` si hay equipos de 6 favoritos. Si no, `incomplete` y el motivo: `reserved_slot` (una regla de presencia necesita un Pokémon que no es favorito), `not_enough_candidates` (menos de 6 válidos) o `no_valid_team` (hay 6 o más, pero no 6 que cumplan juntos las reglas) ([RN-08](../01-ddf/reglas-negocio.md#rn-08)). |
| `score` | Puntuación de los equipos recomendados, que empatan en cabeza. |
| `groups` | Los equipos empatados, ya desempatados con [RN-19](../01-ddf/reglas-negocio.md#rn-19), agrupados por miembros intercambiables ([CA-33](../01-ddf/cuestiones-abiertas.md#resueltas)). `positions` tiene, por cada posición, los Pokémon que la pueden ocupar con sus tipos en el juego; cada combinación es uno de los `teams` del grupo. Un equipo que no se agrupa forma un grupo con una opción por posición. |
| `teams[].breakdown` | Una entrada por regla blanda activa, en orden del catálogo: peso, puntuación de la regla en **porcentaje**, aportación y miembros que cuentan en contra ([RF-09](../01-ddf/requisitos-funcionales.md#rf-09)). Una regla con peso 0 aparece con aportación 0. |
| `teams[].open_slots` | Si el equipo tiene menos de 6: los huecos reservados por una regla de presencia (`rule_id`), uno por regla, y después los libres juntos (`rule_id` nulo), cada uno con **todas** sus sugerencias de mejor a peor y si están verificadas ([CA-31](../01-ddf/cuestiones-abiertas.md#resueltas), [CA-50](../01-ddf/cuestiones-abiertas.md#resueltas)). Con varios huecos libres, cada sugerencia encaja con el equipo, pero no necesariamente con las demás. |
| `discards` | Los favoritos descartados, en orden de la Pokédex Nacional, con la regla, el motivo (`generation`, `game`, `arrival`, `breeding` o `journey`) y su explicación ([RF-10](../01-ddf/requisitos-funcionales.md#rf-10)). `fact_key` es el dato confirmado por el usuario que decidió el descarte, si lo hay. |
| `presence` | El nivel de cada regla de presencia activa ([RN-13](../01-ddf/reglas-negocio.md#rn-13), [RN-14](../01-ddf/reglas-negocio.md#rn-14)): `candidates`, `reserved` o `unmet`, con los Pokémon que la cumplen. |
| `confirmed_facts` | Los datos que confirmó el usuario y que intervienen en la generación, con su valor ([RF-09](../01-ddf/requisitos-funcionales.md#rf-09)). |
| `data_version` | La carga de datos usada, como en `/api/meta`. |

**Puntuaciones enteras** ([CA-51](../01-ddf/cuestiones-abiertas.md#resueltas)): el motor
calcula con fracciones exactas ([ADR-0006](../03-adr/0006-algoritmo-busqueda-exacta.md)) y
decide con ellas el orden y los empates. La API redondea la puntuación de cada equipo al entero
más cercano (las mitades, hacia arriba) y reparte las aportaciones con el **método del mayor
resto**: cada regla recibe la parte entera de su aportación y las unidades que faltan para el
total van a las de mayor parte decimal (a igualdad, a la primera del catálogo). Así siempre
suman la puntuación del equipo. En el ejemplo, la puntuación exacta es 223/12 (18,58): RN-17
aporta 9,58 y recibe la unidad que falta, así que se muestra 1 + 3 + 10 + 5 = 19. Lo que aporta
cada sugerencia (`gain`) también se redondea. Dos equipos que se muestran con el mismo número
no tienen por qué estar empatados.

**Datos pendientes**: si queda algún dato sin confirmar que interviene, la respuesta es `409`
con el mensaje y los mismos datos que muestra la [revisión](#juegos-y-revision-de-datos), con
su estado:

```json
{
  "detail": {
    "message": "Antes de generar hay que confirmar los datos sin verificar que intervienen",
    "pending": [{"fact_key": "mechanic:firered:contests", "status": "pending", "...": "..."}]
  }
}
```

### Hall of Fame

| Método | Ruta | Descripción | Requisitos |
|--------|------|-------------|------------|
| `GET` | `/api/hall-of-fame` | Registros en el orden del recorrido. Filtro: `game`. ✅ | RF-13 |
| `POST` | `/api/hall-of-fame` | Registra un equipo (juego, fecha, notas y de 1 a 6 Pokémon) y lo devuelve con `201`. Guarda los tipos de cada miembro en ese juego. `422` si el juego o algún Pokémon no existen en los datos cargados o en la generación del juego. ✅ | RF-12 |
| `PATCH` | `/api/hall-of-fame/{id}` | Corrige el juego, la fecha, las notas o el equipo. Si cambian el juego o el equipo, vuelve a copiar los tipos. `404` si no existe; `422` como al registrar o si no se indica nada. ✅ | RF-13 |
| `DELETE` | `/api/hall-of-fame/{id}` | Elimina un registro y su equipo: `204`, o `404` si no existe. ✅ | RF-13 |

Petición para registrar un equipo (`notes` es opcional; los miembros, en orden, pueden repetir
forma):

```json
{"game": "leafgreen", "completed_on": "2026-05-01", "notes": "Sin objetos", "members": ["dragonite", "vaporeon", "gengar"]}
```

Cada registro de la respuesta:

```json
{
  "id": 1,
  "game": "leafgreen",
  "game_name": "Verde Hoja",
  "generation": 3,
  "completed_on": "2026-05-01",
  "notes": "Sin objetos",
  "order": 2,
  "last": true,
  "members": [
    {"position": 1, "pokemon": "dragonite", "name": "Dragonite", "types": ["dragon", "flying"]},
    "…"
  ]
}
```

- **Recorrido**: los registros se ordenan por fecha y, a igualdad, por orden de registro
  ([RF-12](../01-ddf/requisitos-funcionales.md#rf-12)). `order` es la posición en el recorrido
  y `last` marca el último juego completado. Con el filtro `game`, `order` sigue siendo la del
  recorrido completo.
- **Juegos**: se puede registrar cualquier juego cargado, también los que no son juego objetivo
  (Rojo, Oro…), porque todos forman parte del recorrido.
- **Tipos**: cada miembro guarda una copia de sus tipos en la generación de ese juego
  ([CA-07](../01-ddf/cuestiones-abiertas.md#resueltas)): Magneton es Eléctrico en Rojo y
  Eléctrico/Acero en Rojo Fuego. Un Pokémon que no existe en la generación del juego no se
  puede registrar.
- **Exclusiones**: al revisar los datos y al generar, el recorrido se pasa al motor, que excluye
  las líneas ya usadas según [RN-16](../01-ddf/reglas-negocio.md#rn-16). Corregir o eliminar un
  registro cambia las exclusiones desde la siguiente petición.

### Metadatos

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/meta` | Versión de la aplicación y de los datos: commit de PokeAPI, fecha de la carga y juegos cargados. `data` es nulo si la carga no dejó registro. ✅ |
