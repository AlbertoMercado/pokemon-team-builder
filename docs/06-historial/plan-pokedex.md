# Plan de la Pokédex

!!! warning "Histórico: no se mantiene"
    Este plan ya se ejecutó y se conserva como historial de cómo y por qué se hizo. No se
    actualiza: lo vigente sobre la Pokédex está en el [DDF](../01-ddf/reglas-negocio.md#reglas-de-la-pokedex),
    el [motor](../02-ddt/motor.md#pokedex-corepokedex), el
    [modelo de datos](../02-ddt/modelo-datos.md#pokedex-y-formas-de-obtencion), el
    [diseño de la web](../02-ddt/web.md#pantallas) y el
    [manual](../04-manual-usuario/web.md#pokedex); lo pendiente, en las
    [issues](https://github.com/AlbertoMercado/pokemon-team-builder/issues).

Plan para completar la Pokédex de los juegos superados
([RF-20](../01-ddf/requisitos-funcionales.md#rf-20) a
[RF-24](../01-ddf/requisitos-funcionales.md#rf-24), reglas
[RN-22 a RN-26](../01-ddf/reglas-negocio.md#reglas-de-la-pokedex)), issue #94. La decisión de
arquitectura sobre los datos está en [ADR-0013](../03-adr/0013-obtencion-pokeapi-y-curados.md).
Ejecutado en la versión 1.5.0; su diseño vigente está en su fuente.

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
  ([arquitectura](../02-ddt/arquitectura.md#reglas-de-dependencia)).
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
[modelo de datos](../02-ddt/modelo-datos.md#pokedex-y-formas-de-obtencion), cómo se cargan en el
[diseño de la carga](../02-ddt/carga-datos.md#pokedex-y-apariciones) y los ficheros curados en
[datos curados](../02-ddt/datos-curados.md#pokedexyaml).

### Motor (`core/pokedex/`)

Implementado en la fase 3: el contexto, la clase de cada método de PokeAPI, el orden de las
formas, la crianza y las claves de cada forma están en el
[motor de reglas](../02-ddt/motor.md#pokedex-corepokedex).

### Datos del usuario y API

Implementados en la fase 4: las tablas, en el
[modelo de datos](../02-ddt/modelo-datos.md#base-de-datos-del-usuario-usersqlite); los endpoints, en la
[referencia de la API](../02-ddt/api-referencia.md) (sección Pokédex), y cómo se usan, en el
[manual](../04-manual-usuario/api.md#pokedex-completar-un-juego-superado).

### Web

Implementada en la fase 5: las pantallas y sus rutas, en el [diseño de la web](../02-ddt/web.md#pantallas),
y cómo se usan, en el [manual](../04-manual-usuario/web.md#pokedex).

## Fases

Cada fase es un PR desde `main`, con sus tests y su documentación
([cómo se documenta](../02-ddt/documentacion.md#en-cada-pr)).

| Fase | Rama | Contenido | Pruebas |
|------|------|-----------|---------|
| 0 | `docs/plan-pokedex` | Este plan y ADR-0013. | — |
| 1 ✅ | `feat/hall-of-fame-unico` | Un registro por juego: migración (se detiene si hay repetidos), `409` al registrar uno ya registrado, juegos registrados fuera de los objetivos y del registro a mano. | Migración con y sin repetidos; API; pantallas; E2E. |
| 2 ✅ | `feat/pokedex-datos` | Tablas y carga de las Pokédex, las apariciones y los datos curados nuevos; nombres en español que faltan. | Extracto sin red; casos conocidos en las comprobaciones de la carga. |
| 3 ✅ | `feat/pokedex-motor` | `core/pokedex/` con RN-22 a RN-26. | Una prueba por regla (`@pytest.mark.rn`) y un escenario real de Rojo Fuego. |
| 4 ✅ | `feat/pokedex-api` | Tablas de `user.sqlite`, migración y endpoints. | API con la base de prueba. |
| 5 ✅ | `feat/pokedex-web` | Las pantallas, el aviso al borrar un registro con Pokédex, manual y CHANGELOG. | Vitest de cada pantalla y E2E. |
| 6 ✅ | `chore/release-1.5.0` | Versión MENOR y cierre de #94. | — |

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

Casos que aparecían en los datos y que el DDF no cubría. Se decidieron al empezar la fase 3
como [CA-82 a CA-87](../01-ddf/cuestiones-abiertas.md#resueltas): lugares de evento, premios
del casino, Sudowoodo y Feebas, y las condiciones de las apariciones (enjambres, avance de la
historia, día de la semana, televisión, amistad y consola virtual) y los regalos a elegir.

### Decisiones tomadas al implementar la fase 3

- **Los regalos a elegir** salieron con los datos y se decidieron como
  [CA-87](../01-ddf/cuestiones-abiertas.md#resueltas): el inicial del juego cuenta como regalo
  que depende del inicial; el resto, como regalo que dice entre cuáles se elige.
- **Todo por especie**: la Pokédex registra especies, así que la API traduce las formas de las
  apariciones, los eventos y las evoluciones a su especie (`deoxys-normal` es `deoxys`).
- **Los saltados no se guardan**: `objective` los recibe de quien llama, como dice
  [CA-77](../01-ddf/cuestiones-abiertas.md#resueltas); la web los pasa a la API
  (`?skipped=…`).
- **Cada forma tiene una clave estable** (`key`), que guardará `pokedex_entry` como la forma
  elegida (fase 4).
- **Los iniciales de cada juego** (hechos en la fase 4): `game_starter` solo tenía los de los
  juegos objetivo, y la Pokédex necesita también los de la 1.ª y la 2.ª generación.

### Decisiones tomadas al implementar la fase 4

- **Iniciales de todos los juegos** en `starters.yaml`, como la forma de su evolución final
  (Pikachu en Amarillo es `raichu`). La API toma la primera etapa de la línea en la generación
  del juego: Pikachu en Amarillo, no Pichu.
- **Las mecánicas que no están cargadas cuentan como presentes**: hoy solo Rojo Fuego y Verde
  Hoja tienen sus mecánicas curadas. Sin esto, Espeon sería imposible en Oro. Es mejor proponer
  una evolución que el juego quizá no permite que esconder una que sí permite. Una mecánica
  pendiente cuenta igual, como en el contexto del generador; una que vale «no» la quita.
- **La Pokédex cuelga del registro del *Hall of Fame***: `pokedex.entry` es su clave foránea
  con borrado en cascada. Cambiar el juego de un registro borra la Pokédex del anterior, como
  borrarlo (CA-68); el aviso de la web está en la fase 5.
- **Sin fila en `pokedex`, la Pokédex no está iniciada**: confirmar la lista inicial la crea.
  Marcar un Pokémon antes responde `409`.
- **Los saltados van en la consulta** (`?skipped=`), sin guardarse (CA-77).
- **Una forma elegida que ya no existe tras una carga nueva se ignora**: la ficha vuelve a
  mostrar la recomendada.
- **Caché de los datos de referencia** (`PokedexReferences`), como la de `GameReferences`: la
  Pokédex de un juego necesita también las apariciones de los que pueden enviarle Pokémon, y
  así se leen una sola vez.

### Decisiones tomadas al implementar la fase 5

- **El aviso al borrar un registro usa `GET /api/pokedex`**, que ya dice si la Pokédex de cada
  registro está empezada y cuántos tiene registrados: la API no cambia. El mismo aviso aparece
  al cambiar el juego de un registro.
- **La web escribe el texto de cada forma** (`web/src/lib/obtention.ts`) con las frases del
  DDF, a partir de los datos de la API, como ya hacía con los métodos de evolución. Un objeto o
  una condición que no conoce se muestra con su identificador.
- **Los saltados viven en la pantalla del objetivo**: salir de ella los olvida (CA-77). Si se
  saltan todos los que quedan, **Volver al primero** empieza de nuevo.
- **La lista inicial tiene un buscador**, porque la Pokédex Nacional tiene 386 Pokémon.
- **El escenario del E2E incluye la Pokédex** de Rojo Fuego y Verde Hoja, sacada del extracto
  de la fase 3. La prueba de la Pokédex registra Verde Hoja y lo borra al final, para no cambiar
  el recorrido de la del juego nuevo.

## Riesgos

- **Errores de PokeAPI**: los que aparezcan se corrigen en datos curados y se avisan aguas arriba.
- **Tamaño**: es la función más grande desde el generador. Si aparece una decisión que el DDF no
  cubre, se pregunta antes de seguir.
