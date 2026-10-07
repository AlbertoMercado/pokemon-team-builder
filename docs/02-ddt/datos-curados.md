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
| [`pokeapi.yaml`](#pokeapiyaml) | Commits fijados del volcado de PokeAPI y del repositorio de imágenes. | `ingest_run.pokeapi_commit`, `ingest_run.sprites_commit` | — |
| [`games.yaml`](#gamesyaml) | Mecánicas de cada juego objetivo. | `game_mechanic` | Rojo Fuego, Verde Hoja |
| [`breeding.yaml`](#breedingyaml) | Bebés que solo nacen con incienso. | `species.requires_incense` | — |
| [`arrival.yaml`](#arrivalyaml) | Regla de llegada de cada juego objetivo. | `game_pokemon.can_arrive` | Rojo Fuego, Verde Hoja |
| [`covers.yaml`](#coversyaml) | Título del fichero de la portada de cada juego en WikiDex (RF-18). | `game.cover`, `game.cover_source` | Los 11 juegos cargados |
| [`key_battles/*.yaml`](#key_battlesyaml) | Lista de combates clave de cada juego y dónde está su equipo en WikiDex. | `key_battle`, `key_battle_pokemon` | Rojo Fuego, Verde Hoja |
| [`evolution_methods.yaml`](#evolution_methodsyaml) | Categoría de cada disparador y condición de evolución de PokeAPI (RN-15, RN-20). **Pendiente de implementar.** | `evolution_method` | — |

Los datos de Rubí, Zafiro y Esmeralda están pendientes (#75, #8).

### `pokeapi.yaml`

**Por qué existe**: la carga de PokeAPI es reproducible porque usa siempre el mismo commit
del volcado CSV ([ADR-0004](../03-adr/0004-pokeapi-volcado-csv.md)) y del repositorio de
imágenes PokeAPI/sprites ([ADR-0010](../03-adr/0010-imagenes-pokemon-cache-local.md)).

```yaml
commit: bc92d3b6029ef1abe9e7ad424c400b338f3c11fe           # volcado CSV
sprites_commit: 8491ffde1b247e4de574d4bb8e24b7bd9fa876fa   # imágenes de los Pokémon
```

Los dos son obligatorios y con el SHA completo, de 40 caracteres. Cambiar un commit es
actualizar los datos o las imágenes: se hace en un PR y se vuelve a ejecutar la
[ingesta](../05-operacion/ingesta.md).

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

### `covers.yaml`

**Por qué existe**: la portada de cada juego es la carátula que muestra la ficha de su artículo
en WikiDex, y los nombres de esos ficheros no siguen ningún patrón (`Carátula de Rojo Fuego.png`,
`Caratula Esmeralda.jpg`, `Pokemon Edición Oro.jpg`), así que se indican a mano
([RF-18](../01-ddf/requisitos-funcionales.md#rf-18),
[ADR-0011](../03-adr/0011-portadas-wikidex-uso-privado.md)).

```yaml
covers:
  firered: "Archivo:Carátula de Rojo Fuego.png"
  emerald: "Archivo:Caratula Esmeralda.jpg"
```

Cada valor es el título completo del fichero en WikiDex, con `Archivo:` y extensión `.png`, `.jpg`
o `.jpeg`; si no, la carga no empieza. Un juego sin entrada se carga sin portada. No va en
`games.yaml`, que solo tiene las mecánicas de los juegos objetivo, porque las portadas son de
todos los juegos cargados. Cambiar un título se hace por PR, y la siguiente carga descarga la
portada nueva. Las imágenes no se guardan en git: solo los títulos.

### `key_battles/*.yaml`

**Por qué existe**: [RN-17](../01-ddf/reglas-negocio.md#rn-17) puntúa los tipos del equipo
frente a los combates clave, y PokeAPI no tiene entrenadores. La lista de combates de cada
juego se mantiene a mano; los equipos se leen de WikiDex
([ingesta](../05-operacion/ingesta.md#wikidex)).

Un fichero por grupo de versiones, porque sus juegos comparten los combates
(`firered-leafgreen.yaml`):

```yaml
games: [firered, leafgreen]
wikidex_section: Pokémon Rojo Fuego y Pokémon Verde Hoja   # sección con sus equipos
battles:                      # en el orden habitual del juego
  - id: brock                 # único en el fichero; minúsculas y guiones
    category: gym_leader      # gym_leader, elite_four, champion, villain_boss o rival_final
    trainer: Brock            # nombre que se muestra
    wikidex_page: Brock       # página de WikiDex del entrenador (no de desambiguación)
    wikidex_team: …           # opcional: rótulo del combate si la sección tiene varios
    rival_starter_lines: […]  # opcional: líneas de los iniciales del rival, que se quitan
    note: …                   # opcional
```

**Dónde está cada equipo en WikiDex**: en la página del entrenador, la sección cuyo título es
exactamente `wikidex_section` tiene una plantilla `{{Equipo}}` por equipo. Si la sección
tiene varios combates, cada uno va precedido de un rótulo (una línea `; En Silph S.A.`), y
`wikidex_team` dice cuál usar. Los rótulos cambian de una página a otra: en Lorelei, Agatha y
Lance el primer combate es «Primer combate», y en Bruno, «Primera vez». Varias plantillas
bajo el mismo rótulo (a menudo en pestañas, una por inicial) son **variantes** del combate.

Si la página, la sección, el rótulo o algún Pokémon no se encuentran, la carga falla con un
mensaje que dice qué combate y qué falta, p. ej.:

```text
WikidexDataError: lorelei (Lorelei): la sección tiene varios combates ['Primer combate', 'Revanchas']: falta wikidex_team
```

Cada combate se carga, para cada juego, como una fila de `key_battle` con:

- `slug`: `<juego>-<id>` (`firered-brock`).
- `order`: su posición en la lista.
- `fact_key`: `battle:<juego>:<id>` (`battle:firered:brock`).
- `origin`: `automatic`, porque el equipo se lee sin ambigüedad o la carga falla.
- `source_page` y `source_revision`: la página y la revisión de WikiDex.

Y sus Pokémon como filas de `key_battle_pokemon`, con su posición y su nivel. Los nombres en
español de WikiDex se traducen a formas cargadas con los nombres de PokeAPI. Antes:

1. Con `rival_starter_lines`, de cada variante se quita el único Pokémon de esas líneas, el
   inicial del rival ([CA-26](../01-ddf/cuestiones-abiertas.md#resueltas)).
2. Si hay variantes, solo se guardan los Pokémon que están en **todas**
   ([CA-38](../01-ddf/cuestiones-abiertas.md#resueltas)): los demás dependen del inicial que
   elija el jugador. Un Pokémon repetido cuenta una vez por variante. Si las variantes no
   tienen nada en común, la carga falla.

Los combates de Rojo Fuego y Verde Hoja son 13: los 8 líderes de gimnasio, el Alto Mando y
Azul, que es el rival y el Campeón y cuenta una vez. Giovanni solo cuenta como líder del
Gimnasio de Ciudad Verde; sus combates como jefe del Team Rocket (Casino Rocket y Silph S.A.)
no son combates clave en Kanto ([CA-39](../01-ddf/cuestiones-abiertas.md#resueltas)).

Equipos cargados en Rojo Fuego (iguales en Verde Hoja):

| # | Combate | Equipo |
|---|---------|--------|
| 1 | Brock | Geodude 12, Onix 14 |
| 2 | Misty | Staryu 18, Starmie 21 |
| 3 | Teniente Surge | Voltorb 21, Pikachu 18, Raichu 24 |
| 4 | Erika | Victreebel 29, Tangela 24, Vileplume 29 |
| 5 | Koga | Koffing 37, Koffing 37, Muk 39, Weezing 43 |
| 6 | Sabrina | Kadabra 38, Venomoth 38, Mr. Mime 37, Alakazam 43 |
| 7 | Blaine | Growlithe 42, Ponyta 40, Rapidash 42, Arcanine 47 |
| 8 | Giovanni | Rhyhorn 45, Dugtrio 42, Nidoking 45, Nidoqueen 44, Rhyhorn 50 |
| 9 | Lorelei | Dewgong 52, Cloyster 51, Slowbro 52, Jynx 54, Lapras 54 |
| 10 | Bruno | Onix 51, Hitmonchan 53, Hitmonlee 53, Onix 54, Machamp 56 |
| 11 | Agatha | Gengar 54, Golbat 54, Haunter 53, Arbok 56, Gengar 58 |
| 12 | Lance | Gyarados 56, Dragonair 54, Dragonair 54, Aerodactyl 58, Dragonite 60 |
| 13 | Azul (Campeón) | Pidgeot 59, Alakazam 57, Rhydon 59 |

En WikiDex, el Campeón tiene tres variantes según el inicial. Sin el inicial, además de los
tres Pokémon comunes tiene Exeggutor y Gyarados, Arcanine y Exeggutor, o Gyarados y Arcanine:
esos no cuentan ([CA-38](../01-ddf/cuestiones-abiertas.md#resueltas)).

### `evolution_methods.yaml`

!!! note "Pendiente de implementar"
    Pendiente en #78. Hasta entonces, la clasificación está en el código de
    `core/evolution.py` ([motor](motor.md#evoluciones-coreevolutionpy)).

**Qué es**: la categoría de cada disparador (`trigger`) y de cada condición de evolución de
PokeAPI: no tedioso, tedioso con su motivo, o aleatorio
([RN-15](../01-ddf/reglas-negocio.md#rn-15), [RN-20](../01-ddf/reglas-negocio.md#rn-20)).

**Por qué existe**: decidir qué es tedioso es una regla de negocio que depende de cómo se
juega, no un dato de PokeAPI. Tenerlo como dato permite que la carga detecte lo que no está
catalogado y quede bloqueada, en lugar de que el motor tenga que adivinarlo
([CA-42](../01-ddf/cuestiones-abiertas.md#resueltas),
[ADR-0008](../03-adr/0008-cargas-bloqueadas.md)).

**Esquema** (orientativo; se fija al implementarlo):

```yaml
triggers:
  level-up: {category: easy}
  use-item: {category: easy}
  trade: {category: tedious, reason: trade}
  shed: {category: tedious, reason: shed}
  spin: {category: tedious, reason: other}
conditions:
  minimum_level: {category: easy}
  gender_id: {category: easy, note: "Se cría hasta que sale el sexo necesario (CA-43)."}
  held_item: {category: easy, note: "Como usar un objeto (CA-43)."}
  time_of_day: {category: tedious, reason: time_of_day, requires_mechanic: day_night_cycle}
  minimum_beauty: {category: tedious, reason: beauty, requires_mechanic: contests}
  percentage_chance: {category: random}
  known_move: {category: tedious, reason: move, unless_learnt_by_level: true}
```

| Campo | Significado |
|-------|-------------|
| `category` | `easy`, `tedious` o `random`. Un método aleatorio también es tedioso. |
| `reason` | Motivo del tedio, para explicarlo en el desglose: `trade`, `shed`, `stats`, `time_of_day`, `beauty`, `location`, `party`, `move` u `other`. |
| `requires_mechanic` | Mecánica del juego sin la cual el paso es imposible en él y, por tanto, tedioso (`games.yaml`). |
| `unless_learnt_by_level` | El paso no es tedioso si el Pokémon aprende el movimiento por nivel a partir del nivel 2 ([CA-32](../01-ddf/cuestiones-abiertas.md#resueltas)). Exige los movimientos por nivel ([CA-45](../01-ddf/cuestiones-abiertas.md#resueltas)). |

Se catalogan los 18 disparadores y todas las condiciones del volcado de PokeAPI, también los
que aún no aparecen en los juegos cargados, con la categoría que les da RN-15. Si la carga
encuentra un disparador o una condición que no está aquí, queda bloqueada y el informe lo
lista con una plantilla para añadirlo a este fichero
([RF-16](../01-ddf/requisitos-funcionales.md#rf-16)). El arquitecto lo completa mediante PR
([protocolo](../05-operacion/ingesta.md#carga-bloqueada)).

## Implementación

| Fichero | Qué hace |
|---------|----------|
| `ingest/sources/curated/schemas.py` | Un modelo pydantic por fichero, con las validaciones de esta página. |
| `ingest/sources/curated/__init__.py` | `read_curated(directorio)` lee y valida todos los ficheros (`CuratedData`). `CuratedSource` carga las mecánicas. |
| `ingest/sources/pokeapi/transform.py` | Usa `CuratedData` para marcar los bebés de incienso y proponer la llegada. |
| `ingest/sources/wikidex/` | Usa la lista de combates de `CuratedData` para leer sus equipos de WikiDex y cargarlos ([ingesta](../05-operacion/ingesta.md#wikidex)). |

Tests en `tests/ingest/test_curated.py` (los ficheros reales del repositorio, los esquemas y la
fuente), en `tests/ingest/test_pokeapi.py` (bebés de incienso y propuestas de llegada) y en
`tests/ingest/test_wikidex.py` (equipos de los combates clave).

## Añadir los datos de un juego

1. Añadir sus mecánicas a `games.yaml` y su regla a `arrival.yaml`. Si no se conoce la regla,
   no añadirla: la llegada queda pendiente y la confirma el usuario.
2. Crear `key_battles/<grupo-de-versiones>.yaml` con sus combates clave y la sección de
   WikiDex de sus equipos. Ejecutar la ingesta: los errores dicen qué página es de
   desambiguación o qué rótulos hay en cada sección, para completar `wikidex_page` y
   `wikidex_team`.
3. Actualizar las comprobaciones de la carga (`ingest/checks.py`) y esta página.
4. Ejecutar la ingesta y revisar el informe.
