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

| Tabla | Contenido | Origen |
|-------|-----------|--------|
| `pokedex`, `pokedex_number` | Las Pokédex y el número de cada especie en ellas. | PokeAPI |
| `game_pokedex` | Qué Pokédex usa cada juego (RN-22). | Curado |
| `location`, `encounter` | Los lugares, con su nombre en español, y cada aparición: juego, lugar, Pokémon, método, probabilidad por zona y método, niveles y condiciones. | PokeAPI; los nombres que faltan, curados |
| `game_transfer` | Qué juegos pueden enviar Pokémon a cuáles, y con qué límite de especies (RN-25). | Curado |
| `special_obtention` | Pokémon de evento, solo de spin-offs, fósiles (Fósil y lugar donde se revive) y regalos que dependen del inicial. | Curado |

Cada método de PokeAPI pasa a una de las clases de [RN-26](../01-ddf/reglas-negocio.md#rn-26):

| Clase | Métodos de PokeAPI |
|-------|--------------------|
| Regalo | `gift`, `gift-egg`, salvo los fósiles |
| Intercambio con PNJ | `npc-trade` |
| Fósil | los `gift` marcados como fósil en los datos curados |
| Estático (100 %) | `static`, `pokeflute`, `devon-scope` |
| Salvaje, por este orden a igual probabilidad | `walk`; `surf`; `seaweed`; `old-rod`; `good-rod`; `super-rod`; `rock-smash` y `headbutt-*` |
| Errante | `roaming-grass`, `roaming-water` |
| Se omite (spin-off) | `colosseum-bonus-disc-*` y similares |

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
| 1 | `feat/hall-of-fame-unico` | Un registro por juego: migración (se detiene si hay repetidos), `409` al registrar uno ya registrado, juegos registrados fuera de los objetivos y del registro a mano, aviso al borrar. | Migración con y sin repetidos; API; pantallas. |
| 2 | `feat/pokedex-datos` | Tablas y carga de las Pokédex, las apariciones y los datos curados nuevos; nombres en español que faltan. | Extracto sin red; casos conocidos en las comprobaciones de la carga. |
| 3 | `feat/pokedex-motor` | `core/pokedex/` con RN-22 a RN-26. | Una prueba por regla (`@pytest.mark.rn`) y un escenario real de Rojo Fuego. |
| 4 | `feat/pokedex-api` | Tablas de `user.sqlite`, migración y endpoints. | API con la base de prueba. |
| 5 | `feat/pokedex-web` | Las pantallas, manual y CHANGELOG. | Vitest de cada pantalla y E2E. |
| 6 | `chore/release-X.Y.0` | Versión MENOR y cierre de #94. | — |

## Pendiente de decidir

Casos que el DDF no cubre y que salieron al comprobar los datos. Se decidirán antes de la fase
que los necesita:

- **Errantes que dependen del inicial**: en Rojo Fuego y Verde Hoja, el perro legendario errante
  depende del inicial elegido. ¿Cuenta como errante o como un regalo que depende del inicial,
  casi al final ([RN-24](../01-ddf/reglas-negocio.md#rn-24))? (Fase 3.)
- **Condiciones de aparición**: en la 2.ª generación la probabilidad cambia con la hora (mañana,
  día y noche), y hay enjambres y otras condiciones. ¿Qué probabilidad cuenta para elegir el
  lugar más sencillo? (Fase 3.)

## Riesgos

- **Nombres en español**: unos 150 lugares de Kanto, Johto y las Islas Sete hay que traducirlos a
  mano una vez. Mientras falte uno, la carga lo dice y se usa el nombre en inglés.
- **Errores de PokeAPI**: los que aparezcan se corrigen en datos curados y se avisan aguas arriba.
- **Tamaño**: es la función más grande desde el generador. Si aparece una decisión que el DDF no
  cubre, se pregunta antes de seguir.
