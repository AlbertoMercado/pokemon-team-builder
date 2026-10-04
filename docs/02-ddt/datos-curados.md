# Datos curados

Datos que no están en ninguna fuente, o que no se pueden deducir con certeza, y que por eso
mantiene una persona en ficheros YAML dentro del repositorio
([ADR-0005](../03-adr/0005-datos-curados-yaml.md)). Esta página describe cada fichero: qué
es, por qué existe, su esquema y cómo lo usa la ingesta.

## Principios

- **En git y por PR**: los ficheros están en `data/curated/` y se cambian como el código, con
  historial y revisión.
- **Validados**: la ingesta valida cada fichero con un modelo pydantic
  (`ingest/sources/curated/schemas.py`). Una clave desconocida (p. ej., una errata), un tipo
  incorrecto o un valor incoherente hacen fallar la carga, con el nombre del fichero y el
  motivo:

    ```text
    ERROR en los datos curados; no se ha cargado nada.
      - data/curated/arrival.yaml: 1 validation error for ArrivalFile …
    ```

- **Con su origen**: los valores que pueden no ser fiables llevan `origin` (`automatic`,
  `inferred` o `pending`), como el resto de datos revisables. Los inferidos y los pendientes
  los confirma el usuario antes de generar ([RN-18](../01-ddf/reglas-negocio.md#rn-18)).
- **Comentados**: cada fichero empieza con un comentario que dice qué es y remite a esta
  página. Los valores discutibles llevan una nota (`note`) con el motivo.
- **Identificadores de PokeAPI**: juegos (`firered`), especies (`azurill`), Pokédex (`kanto`)
  y objetos (`sea-incense`) se escriben con su identificador de PokeAPI.

## Ficheros

| Fichero | Qué contiene | Se carga en | Juegos con datos |
|---------|--------------|-------------|------------------|
| [`pokeapi.yaml`](#pokeapiyaml) | Commit fijado del volcado de PokeAPI. | `ingest_run.pokeapi_commit` | — |
| [`games.yaml`](#gamesyaml) | Mecánicas de cada juego objetivo. | `game_mechanic` | Rojo Fuego, Verde Hoja |
| [`breeding.yaml`](#breedingyaml) | Bebés que solo nacen con incienso. | `species.requires_incense` | — |
| [`arrival.yaml`](#arrivalyaml) | Regla de llegada de cada juego objetivo. | `game_pokemon.can_arrive` | Rojo Fuego, Verde Hoja |
| [`key_battles/*.yaml`](#key_battlesyaml) | Lista de combates clave de cada juego. | `key_battle` | Rojo Fuego, Verde Hoja |

Rubí, Zafiro y Esmeralda se completan en la fase 6 del
[plan de carga](plan-carga-datos.md#fases). Mientras tanto, sus datos quedan pendientes.

### `pokeapi.yaml`

**Por qué existe**: la carga de PokeAPI es reproducible porque usa siempre el mismo commit
del volcado CSV ([ADR-0004](../03-adr/0004-pokeapi-volcado-csv.md)).

```yaml
commit: bc92d3b6029ef1abe9e7ad424c400b338f3c11fe   # SHA completo, 40 caracteres
```

Cambiar el commit es actualizar los datos de PokeAPI: se hace en un PR y se vuelve a
ejecutar la [ingesta](../05-operacion/ingesta.md).

### `games.yaml`

**Por qué existe**: algunas evoluciones dependen de mecánicas que no todos los juegos tienen.
Sin reloj no hay evoluciones por hora del día, y sin concursos no se puede subir la belleza
([RN-15](../01-ddf/reglas-negocio.md#rn-15)). PokeAPI no tiene estos datos.

```yaml
games:
  firered:                    # juego objetivo
    day_night_cycle:          # mecánica: day_night_cycle o contests
      value: false            # sí/no; falta solo si origin es pending
      origin: inferred        # automatic, inferred o pending
      note: No tiene reloj…   # opcional
```

| Mecánica | Significado | Evoluciones afectadas en las generaciones 1 a 3 |
|----------|-------------|--------------------------------------------------|
| `day_night_cycle` | El juego tiene reloj y distingue el día de la noche. | Eevee → Espeon o Umbreon |
| `contests` | El juego tiene concursos y se puede subir la belleza. | Feebas → Milotic |

Cada mecánica se carga como una fila de `game_mechanic` con la clave revisable
`mechanic:<juego>:<mecánica>` ([modelo de datos](modelo-datos.md#datos-revisables-fact_key)).

### `breeding.yaml`

**Por qué existe**: en algunas líneas, el bebé solo nace si un progenitor lleva un incienso.
Por [CA-36](../01-ddf/cuestiones-abiertas.md#resueltas), en esas líneas la etapa que llega al
juego objetivo es la que nace sin incienso. PokeAPI no indica qué bebés necesitan incienso.

```yaml
incense_babies:
  azurill: sea-incense    # <bebé>: <incienso>
  wynaut: lax-incense
```

La ingesta marca esas especies con `species.requires_incense` y falla si alguna no es un bebé
cargado. La regla se aplica al proponer la llegada (abajo) y, más adelante, en
`core/breeding.py`.

### `arrival.yaml`

**Por qué existe**: un Pokémon solo es candidato si la etapa que nace del huevo puede llegar
al juego objetivo y evolucionar antes de completarlo
([RN-03](../01-ddf/reglas-negocio.md#rn-03),
[CA-28](../01-ddf/cuestiones-abiertas.md#abiertas)). Eso depende de restricciones de cada
juego que no están en ninguna fuente, así que la ingesta propone el dato con una regla por
juego.

```yaml
games:
  firered:
    regional_pokedex: kanto   # Pokédex de PokeAPI; falta solo si origin es pending
    origin: inferred          # inferred o pending
    note: Antes de la Pokédex Nacional…
```

**Regla**: un Pokémon puede llegar si la etapa que nace del huevo y **todas las etapas hasta
él** están en `regional_pokedex`. La etapa que nace del huevo es la primera de su línea entre
las especies cargadas, salvo los bebés de incienso, que se saltan.

Resultado en Rojo Fuego y Verde Hoja, con la Pokédex de Kanto: pueden llegar 140 Pokémon (los
151 de Kanto menos 11). No llegan los que nacen como bebé de la 2.ª generación: Pikachu y
Raichu (Pichu), Clefairy y Clefable (Cleffa), Jigglypuff y Wigglytuff (Igglybuff), Jynx
(Smoochum), Electabuzz (Elekid), Magmar (Magby), y Hitmonlee y Hitmonchan (Tyrogue). Tampoco
las evoluciones de la 2.ª generación, como Crobat o Espeon
([restricciones comprobadas](datos-requeridos.md#rojo-fuego-y-verde-hoja-comprobado)).

Las propuestas son **inferidas**: el usuario las confirma. Un juego objetivo sin regla queda
con la llegada **pendiente**. Una regla para un juego que no es juego objetivo hace fallar la
carga.

### `key_battles/*.yaml`

**Por qué existe**: [RN-17](../01-ddf/reglas-negocio.md#rn-17) puntúa los tipos del equipo
frente a los combates clave, y PokeAPI no tiene entrenadores. La lista de combates de cada
juego se mantiene a mano; los equipos se leen de WikiDex (fase 5).

Un fichero por grupo de versiones, porque sus juegos comparten los combates
(`firered-leafgreen.yaml`):

```yaml
games: [firered, leafgreen]
battles:                      # en el orden habitual del juego
  - id: brock                 # único en el fichero; minúsculas y guiones
    category: gym_leader      # gym_leader, elite_four, champion, villain_boss o rival_final
    trainer: Brock            # nombre que se muestra
    wikidex_page: Brock       # página de WikiDex con su equipo
    note: …                   # opcional
```

Cada combate se carga, para cada juego, como una fila de `key_battle` con:

- `slug`: `<juego>-<id>` (`firered-brock`).
- `order`: su posición en la lista.
- `fact_key`: `battle:<juego>:<id>` (`battle:firered:brock`).
- `origin`: `pending` hasta que la fase 5 cargue su equipo.

Los combates de Rojo Fuego y Verde Hoja son 15: los 8 líderes de gimnasio (Giovanni es el
octavo), Giovanni como jefe del Team Rocket en el Escondite Rocket y en Silph S.A., el Alto
Mando y Azul, que es el rival y el Campeón (cuenta una vez y sin su inicial,
[CA-26](../01-ddf/cuestiones-abiertas.md#resueltas)).

!!! warning "Pendiente de confirmar"
    Que el combate contra Giovanni en Silph S.A. sea obligatorio. Si no lo es, se quita de la
    lista, porque los combates clave son solo los obligatorios.

## Implementación

| Fichero | Qué hace |
|---------|----------|
| `ingest/sources/curated/schemas.py` | Un modelo pydantic por fichero, con las validaciones de esta página. |
| `ingest/sources/curated/__init__.py` | `read_curated(directorio)` lee y valida todos los ficheros (`CuratedData`). `CuratedSource` carga las mecánicas y los combates clave. |
| `ingest/sources/pokeapi/transform.py` | Usa `CuratedData` para marcar los bebés de incienso y proponer la llegada. |

Tests en `tests/ingest/test_curated.py` (los ficheros reales del repositorio, los esquemas y la
fuente) y en `tests/ingest/test_pokeapi.py` (bebés de incienso y propuestas de llegada).

## Añadir los datos de un juego

1. Añadir sus mecánicas a `games.yaml` y su regla a `arrival.yaml`. Si no se conoce la regla,
   no añadirla: la llegada queda pendiente y la confirma el usuario.
2. Crear `key_battles/<grupo-de-versiones>.yaml` con sus combates clave, comprobando que cada
   `wikidex_page` existe en WikiDex.
3. Actualizar las comprobaciones de la carga (`ingest/checks.py`) y esta página.
4. Ejecutar la ingesta y revisar el informe.
