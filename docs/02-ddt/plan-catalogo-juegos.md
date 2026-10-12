# Plan del catálogo de juegos

Plan para que el usuario elija en un **catálogo de juegos** cuáles pueden ser juego objetivo
([RF-25](../01-ddf/requisitos-funcionales.md#rf-25), [RF-05](../01-ddf/requisitos-funcionales.md#rf-05),
[CA-90 a CA-93](../01-ddf/cuestiones-abiertas.md#resueltas)). Lo pendiente de cada fase está en
su PR; al terminar, este plan se archiva en el [historial](../06-historial/index.md).

## Alcance

**Dentro**:

| Bloque | Requisitos y decisiones |
|--------|-------------------------|
| El catálogo: los 36 juegos de la saga principal y los Leyendas que pueden recibir un Pokémon criado | RF-25, CA-90, CA-91 |
| Qué le falta a cada juego para ser juego objetivo: recibir un Pokémon criado, datos completos y ser jugable | RF-05, CA-29, CA-67, CA-91, CA-92 |
| La selección del usuario y su respuesta sobre si un juego es jugable, en `user.sqlite` | RF-25, CA-92, CA-93 |
| El juego objetivo pasa a ser el seleccionado que cumple las condiciones; Nuevo juego, la revisión y la generación lo usan | RF-05, CA-93 |
| La pantalla **Juegos** de la web | RF-25 |

**Fuera**:

- Cargar los juegos de la 4.ª generación en adelante: el catálogo los muestra con el motivo «su
  generación todavía no se carga». Ampliar la carga es otra función (y #114 para su llegada).
- Las portadas de los juegos que no se cargan: el catálogo muestra la portada solo si el juego
  está cargado y la tiene ([RF-18](../01-ddf/requisitos-funcionales.md#rf-18)).
- Let's Go Pikachu y Let's Go Eevee, los spin-offs (Colosseum, XD), los DLC y las ediciones
  japonesas ([CA-90](../01-ddf/cuestiones-abiertas.md#resueltas)).

## Principios

- **El usuario decide, la aplicación comprueba**: un juego solo se selecciona si cumple las
  condiciones de RF-05; si no, se dice qué le falta.
- **Lo que se sabe, como dato; lo que no, se pregunta**: el catálogo es un dato curado. De si un
  juego es jugable en un sistema actual solo se sabe con certeza en los de Switch; del resto se
  pregunta al usuario y se guarda su respuesta ([CA-92](../01-ddf/cuestiones-abiertas.md#resueltas)).
- **Núcleo puro**: la decisión de si un juego puede ser juego objetivo, y por qué no, va en
  `core/`, sin red ni base de datos ([arquitectura](arquitectura.md#reglas-de-dependencia)).
- **Datos separados**: lo que es de todos (el catálogo) va en `reference.sqlite`; lo del usuario
  (selección y respuestas), en `user.sqlite`
  ([ADR-0003](../03-adr/0003-dos-bases-de-datos-sqlite.md)).

## Comprobaciones previas

Hechas el 2026-10-12 con el volcado CSV de PokeAPI del commit fijado (`bc92d3b`):

| Comprobación | Resultado |
|--------------|-----------|
| Los 36 juegos en PokeAPI | Sí, todos en `versions.csv`, también Leyendas Z-A (`legends-za`, grupo de versiones `legends-za`, 9.ª generación). El catálogo usa sus identificadores. |
| Juegos de PokeAPI que no entran | Let's Go Pikachu y Eevee, Colosseum y XD, los DLC (`the-isle-of-armor`, `the-crown-tundra`, `the-teal-mask`, `the-indigo-disk`), `mega-dimension`, `champions` y las ediciones japonesas (`red-japan`, `green-japan`, `blue-japan`). |
| Juegos cargados hoy | Los 11 de las generaciones 1 a 3; son juego objetivo (completos) los 5 de la 3.ª. |

## Diseño

### Datos curados y de referencia (fase 2)

`data/curated/catalog.yaml`, en orden de lanzamiento:

```yaml
games:
  - game: firered                 # identificador de PokeAPI (versions.csv)
    name: Rojo Fuego
    generation: 3
    platform: game_boy_advance    # game_boy, game_boy_color, game_boy_advance, ds, 3ds, switch
    receives_bred: true           # puede recibir un Pokémon criado (CA-29, CA-91)
    playable_now: unknown         # yes o unknown (CA-92)
    note: …
```

- Los de Switch, `playable_now: yes`; el resto, `unknown`. Rojo, Azul y Amarillo,
  `receives_bred: false`.
- La ingesta lo carga en una tabla nueva (`catalog_game`), aparte de `game`, porque los juegos de
  las generaciones que no se cargan no tienen grupo de versiones ni generación en
  `reference.sqlite`. Guarda también qué le falta a cada uno para estar completo: la lista de
  `ingest/targets.py` o «su generación todavía no se carga».
- `game.is_target` sigue marcando los juegos completos; no se renombra, para no tocar la API antes
  de la fase 3, que deja de usarlo como juego objetivo.
- Comprobaciones de la carga: que estén los 36, que existan en PokeAPI y que todo juego cargado
  esté en el catálogo.

### `core/` (fase 3)

Una función pura que, con el juego del catálogo, la selección y la respuesta del usuario y si
está superado, dice si es juego objetivo y, si no, los motivos en el orden de RF-25: no recibe
un Pokémon criado; le faltan datos (cuáles); no se sabe si es jugable (hay que preguntar); no es
jugable; está superado.

### `user.sqlite` y API (fase 3)

- Migración de Alembic con una tabla de elecciones por juego: si está seleccionado y la
  respuesta del usuario sobre si es jugable (sí, no o sin responder). Empieza vacía: al
  actualizar no queda ningún juego seleccionado
  ([CA-93](../01-ddf/cuestiones-abiertas.md#resueltas)).
- `GET` del catálogo: cada juego con su nombre, generación, plataforma, portada si la tiene, si
  está seleccionado, si es juego objetivo y los motivos si no lo es.
- `PUT` de un juego: seleccionarlo o quitarlo y responder si es jugable. Seleccionar uno que no
  cumple las condiciones responde `409` con los motivos, y uno de jugabilidad desconocida pide la
  respuesta.
- `/api/games` (Nuevo juego), la revisión y la generación usan la nueva definición de juego
  objetivo. El *Hall of Fame* sigue admitiendo cualquier juego cargado.

### Web (fase 4)

- Pantalla **Juegos** en la navegación: los juegos por generación, cada uno con su portada si la
  tiene, su plataforma, si está seleccionado y, si no se puede seleccionar, el motivo. Al
  seleccionar uno de jugabilidad desconocida, la web pregunta «¿Puedes jugarlo en un sistema
  actual de Nintendo?».
- **Nuevo juego**: si no hay ningún juego objetivo, explica por qué y enlaza al catálogo.
- Pruebas: pantallas con la API simulada, el flujo de nuevo juego E2E empezando por seleccionar
  Rojo Fuego en el catálogo, y la maquetación de las tarjetas del catálogo
  (`e2e/layout.spec.ts`).

## Fases

| Fase | Rama | Qué | Documentación |
|------|------|-----|---------------|
| 1 ✅ | `docs/catalogo-juegos` | RF-25, RF-05, CA-29 y CA-90 a CA-93 en el DDF, y este plan. | DDF y este plan |
| 2 ✅ | `feat/catalogo-juegos-datos` | `catalog.yaml`, la tabla `catalog_game`, qué le falta a cada juego y las comprobaciones de la carga. | Datos curados, modelo de datos, diseño de la carga, Operación de la ingesta |
| 3 ✅ | `feat/catalogo-juegos-api` | La decisión en `core/`, la migración de `user.sqlite` y la API; `/api/games`, la revisión y la generación con la nueva definición. | Motor, modelo de datos, referencia y DDT de la API, manual de la API |
| 4 ✅ | `feat/catalogo-juegos-web` | La pantalla Juegos, Nuevo juego sin juegos objetivo y las pruebas. | Diseño de la web, manual de la web, CHANGELOG |

Al terminar la fase 4, el CHANGELOG avisa de que hay que repetir la carga y elegir los juegos en
el catálogo: Nuevo juego queda vacío hasta entonces.
