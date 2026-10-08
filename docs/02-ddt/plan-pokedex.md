# Plan de la Pokédex

Plan para completar la Pokédex de los juegos superados
([RF-20](../01-ddf/requisitos-funcionales.md#rf-20) a
[RF-24](../01-ddf/requisitos-funcionales.md#rf-24), reglas
[RN-22 a RN-26](../01-ddf/reglas-negocio.md#reglas-de-la-pokedex)), issue #94. La decisión de
arquitectura sobre los datos está en [ADR-0013](../03-adr/0013-obtencion-pokeapi-y-curados.md).
Cuando se ejecute, este plan pasará al [historial](../06-historial/index.md) y su diseño
vigente, a su fuente.

## Alcance

**Dentro**:

| Bloque | Requisitos y decisiones |
|--------|-------------------------|
| Un registro por juego en el *Hall of Fame*; los juegos registrados dejan de ser objetivo | RF-05, RF-12, RF-13, [CA-68](../01-ddf/cuestiones-abiertas.md#resueltas) |
| La carga de las Pokédex, las apariciones y los datos curados nuevos | RN-22, RN-25, RN-26, CA-72, CA-78, ADR-0013 |
| El progreso, el Pokémon objetivo y las formas de obtención en `core/` | RN-22 a RN-26 |
| El estado de cada Pokédex en `user.sqlite` y su API | RF-20 a RF-24 |
| La sección Pokédex de la web | RF-20 a RF-24 |

**Fuera**: los juegos que no están cargados (de la 4.ª generación en adelante) y los que PokeAPI
no cubre, los spin-offs ([CA-73](../01-ddf/cuestiones-abiertas.md#resueltas)) y cualquier
efecto de la Pokédex en la generación de equipos
([CA-79](../01-ddf/cuestiones-abiertas.md#resueltas)).

## Principios

- **Función aparte**: la Pokédex no toca el generador. Comparte con él el *Hall of Fame* y los
  datos de referencia.
- **Núcleo puro**: las reglas van en `core/`, sin red ni base de datos, como el motor
  ([arquitectura](arquitectura.md#reglas-de-dependencia)).
- **Datos sin red**: todo sale de la carga (PokeAPI y datos curados); la aplicación no consulta
  nada externo.
- **Lo curado, mínimo**: solo lo que PokeAPI no tiene (ADR-0013).

## Comprobaciones previas

Hechas el 2026-10-07 con el volcado CSV de PokeAPI del commit fijado (`bc92d3b`):

| Comprobación | Resultado |
|--------------|-----------|
| Apariciones de los 11 juegos | Sí: de 891 filas en Rojo a 3183 en Cristal; 2117 en Rojo Fuego (140 especies). |
| Métodos en las generaciones 1 a 3 | Andar, surfear, caña vieja, buena y súper, golpe roca, cabezazo (alto, normal y bajo), buceo (`seaweed`), Detector Devon, Poké Flauta, regalo, huevo de regalo, estático, intercambio con PNJ y errante. También los del disco extra de Colosseum, que son de spin-off. |
| Casos conocidos en Rojo Fuego | Eevee, regalo; Lapras, regalo y surf; Hitmonlee, regalo; Omanyte, Kabuto y Aerodactyl, regalo (son los fósiles); Snorlax, Poké Flauta; Zapdos, estático; Raikou y Entei, errantes; Ekans, salvaje; Sandshrew y Mew, ninguno (exclusivo de Verde Hoja y evento). |
| Casos conocidos en Oro | Raikou, Entei y Suicune, errantes; Eevee, regalo; Togepi, huevo de regalo. |
| Pokédex | Nacional (1025), Kanto (151), Johto original (251) y Hoenn (202). |
| Nombres de los lugares en español | Casi todos en Hoenn (64 de 68 en Rubí); **ninguno** en Kanto, Johto ni las Islas Sete. |

## Diseño

### Datos de referencia

Implementados en la fase 2: las tablas están en el
[modelo de datos](modelo-datos.md#pokedex-y-formas-de-obtencion), cómo se cargan en el
[diseño de la carga](carga-datos.md#pokedex-y-apariciones) y los ficheros curados en
[datos curados](datos-curados.md#pokedexyaml).

Cada método de PokeAPI pasa a una de las clases de [RN-26](../01-ddf/reglas-negocio.md#rn-26)
en `core/` (fase 3):

| Clase | Métodos y condiciones de PokeAPI |
|-------|----------------------------------|
| Regalo | `gift`, `gift-egg`, salvo los fósiles |
| Intercambio con PNJ | `npc-trade` |
| Fósil | `gift` con una condición `item-*-fossil` u `item-old-amber` |
| Estático (100 %) | `static`, `pokeflute`, `devon-scope` |
| Salvaje, por este orden a igual probabilidad | `walk`; `surf`; `seaweed`; `old-rod`; `good-rod`; `super-rod`; `rock-smash` y `headbutt-*` |
| Errante | `roaming-grass`, `roaming-water`; con `starter-*`, depende del inicial (CA-80) |
| Se omite (spin-off) | `colosseum-bonus-disc-*`, `pokemon-channel-pal` |
| Por decidir en la fase 3 | Ver [abajo](#decisiones-tomadas-al-implementar-la-fase-2) |

### Motor (`core/pokedex/`)

Funciones puras sobre un contexto de la Pokédex de un juego: sus Pokémon, los registrados y los
imposibles, las Pokédex de los otros juegos superados, las apariciones, las líneas evolutivas
con sus métodos, la crianza y los datos curados.

- `progress`: porcentaje redondeado hacia abajo, estado y número de imposibles (RN-22).
- `objective`: el primero sin registrar ni imposible, sin los saltados (RN-23).
- `obtention_methods`: todas las formas de obtener un Pokémon, ordenadas por RN-24 a RN-26, con
  su detalle (lugar y probabilidad, juego de origen, método de evolución, Pokémon que hay que
  criar o evolucionar) y si es imposible de forma automática (RN-25).

### Datos del usuario y API

| Tabla de `user.sqlite` | Contenido |
|------------------------|-----------|
| `pokedex` | Una por juego superado: si ya se marcó la lista inicial. |
| `pokedex_entry` | Por Pokémon: registrado o imposible, y la forma de obtención elegida. |

Se borran con su registro del *Hall of Fame*. La API sigue sus
[convenciones](api.md):

| Endpoint | Para qué |
|----------|----------|
| `GET /api/pokedex` | Juegos superados con su progreso (RF-20). |
| `GET /api/pokedex/{game}` | La Pokédex de un juego, con sus registrados e imposibles (RF-21, RF-24). |
| `PUT /api/pokedex/{game}/initial` | La lista inicial (RF-21). |
| `GET /api/pokedex/{game}/objective?skipped=…` | El Pokémon objetivo; los saltados los pasa la web y no se guardan (RN-23). |
| `GET /api/pokedex/{game}/pokemon/{species}` | La ficha con todas sus formas de obtención (RF-22, RF-23). |
| `PUT /api/pokedex/{game}/pokemon/{species}` y `DELETE` | Registrar, marcar como imposible, elegir una forma y desmarcar (RF-22 a RF-24). |

### Web

- **Pokédex** en el menú: la lista de juegos superados con su progreso y estado.
- La lista inicial, la ficha del Pokémon objetivo con sus acciones y enlaces, las otras formas
  de obtención y el detalle de registrados e imposibles.
- En el *Hall of Fame*, el aviso al borrar un registro con Pokédex.

## Fases

Cada fase es un PR desde `main`, con sus tests y su documentación
([cómo se documenta](documentacion.md#en-cada-pr)).

| Fase | Rama | Contenido | Pruebas |
|------|------|-----------|---------|
| 0 | `docs/plan-pokedex` | Este plan y ADR-0013. | — |
| 1 ✅ | `feat/hall-of-fame-unico` | Un registro por juego: migración (se detiene si hay repetidos), `409` al registrar uno ya registrado, juegos registrados fuera de los objetivos y del registro a mano. | Migración con y sin repetidos; API; pantallas; E2E. |
| 2 ✅ | `feat/pokedex-datos` | Tablas y carga de las Pokédex, las apariciones y los datos curados nuevos; nombres en español que faltan. | Extracto sin red; casos conocidos en las comprobaciones de la carga. |
| 3 | `feat/pokedex-motor` | `core/pokedex/` con RN-22 a RN-26. | Una prueba por regla (`@pytest.mark.rn`) y un escenario real de Rojo Fuego. |
| 4 | `feat/pokedex-api` | Tablas de `user.sqlite`, migración y endpoints. | API con la base de prueba. |
| 5 | `feat/pokedex-web` | Las pantallas, el aviso al borrar un registro con Pokédex, manual y CHANGELOG. | Vitest de cada pantalla y E2E. |
| 6 | `chore/release-X.Y.0` | Versión MENOR y cierre de #94. | — |

## Decisiones tomadas al planificar

Casos que el DDF no cubría y que salieron al comprobar los datos:

- **Errantes que dependen del inicial** (el perro legendario de Rojo Fuego y Verde Hoja): cuentan
  como errantes e indican de qué inicial dependen
  ([CA-80](../01-ddf/cuestiones-abiertas.md#resueltas)). El inicial de cada errante va en los
  datos curados.
- **Probabilidad que cambia con la hora** (2.ª generación): cuenta la mayor e indica el momento
  ([CA-81](../01-ddf/cuestiones-abiertas.md#resueltas)). El resto de condiciones (enjambres,
  radio…) se decidirán si aparecen en la fase 3.

### Decisiones tomadas al implementar la fase 1

- **El `409` de un juego ya registrado lleva su registro** (`CompletedGameOut`, con
  `hall_of_fame_entry`), para distinguirlo del de los datos pendientes: la web lleva a la
  revisión solo con este último.
- **Tras registrar desde el resultado ya no se genera otra vez**: el juego queda completado y el
  resultado lo dice. El E2E comprueba que **Nuevo juego** deja de ofrecerlo.
- **`GET /api/games?all=true` añade `completed`**, y `target` es falso en un juego completado.
- **El aviso al borrar un registro pasa a la fase 5**, porque solo tiene sentido cuando haya
  Pokédex que borrar.
- **La simulación de la API de la web** aplica la misma regla, y su registro inicial del *Hall
  of Fame* pasa a ser de Verde Hoja para que Rojo Fuego siga siendo juego objetivo.

### Decisiones tomadas al implementar la fase 2

- **Fósiles y errantes según el inicial, de PokeAPI**: PokeAPI sí los distingue, con las
  condiciones del regalo (`item-helix-fossil`) y del errante (`starter-squirtle`). No van en
  los datos curados, que se quedan en lo que PokeAPI no tiene (ADR-0013).
- **Sin `special_obtention`**: los datos curados son cuatro ficheros, uno por tema:
  `pokedex.yaml`, `transfers.yaml`, `events.yaml` (los singulares) y `locations.yaml` (nombres
  en español y objetos de evento de los lugares).
- **Las apariciones se guardan como las da PokeAPI**, con su método y sus condiciones, y se
  cargan también las de los spin-offs: clasificarlas es de `core/`, como los pasos de evolución.
  La carga solo comprueba que no hay métodos sin clasificar.
- **Probabilidad unida por Pokémon, zona, método y condiciones**: se suman los huecos y se limita
  al 100 %.
- **Lugares a los que solo se llega por evento** (Roca Ombligo, Isla Origen, Isla Suprema e Isla
  del Sur): PokeAPI los da como estáticos; `location.event_item` dice con qué objeto de evento se
  llega.
- **Los 146 nombres en español que faltaban**, comprobados en WikiDex: la carga real no deja
  ningún lugar sin nombre.

Casos que aparecen en los datos y que el DDF no cubre. Se decidirán al empezar la fase 3, antes
de clasificarlos:

- **Lugares de evento**: ¿sus apariciones cuentan como evento (forma 7 de RN-24) o como
  estáticas?
- **Premios del casino** (`gift` con `coins-*`, como el Porygon de Ciudad Azulona): ¿regalo?
- **Métodos sin clase**: `squirt-bottle` y `wailmer-pail` (Sudowoodo), `feebas-tile-fishing`.
- **Condiciones**: enjambres (`swarm-*`), avance de la historia (`story-progress-*`), día de la
  semana (Lapras los viernes en la Cueva Unión), opción de la televisión (Latios o Latias en
  Esmeralda), amistad del primer Pokémon (el huevo de Togepi), consola virtual (Celebi en
  Cristal).

## Riesgos

- **Errores de PokeAPI**: los que aparezcan se corrigen en datos curados y se avisan aguas arriba.
- **Tamaño**: es la función más grande desde el generador. Si aparece una decisión que el DDF no
  cubre, se pregunta antes de seguir.
