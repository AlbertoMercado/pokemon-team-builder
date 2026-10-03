# Datos requeridos por las reglas

!!! warning "Borrador"
    Se deriva del catálogo de reglas del [DDF](../01-ddf/reglas-negocio.md) (RN-01 a RN-17) y
    sirve de base para el modelo de datos. Todavía no es el modelo definitivo: no fija tablas,
    claves ni tipos.

## Resumen por regla

| Regla | Datos que necesita |
|-------|--------------------|
| RN-02, RN-09 | Favoritos del usuario (forma concreta). Cadena evolutiva para conocer las preevoluciones. |
| RN-03 | Generación de cada juego. Pokémon (por forma) que pueden estar en cada juego, también por transferencia. Etapa que nace del huevo en cada línea. Restricciones de llegada y de evolución antes de completar cada juego ([CA-28](../01-ddf/cuestiones-abiertas.md#abiertas)). |
| RN-05, RN-06 | Especie de cada forma y si la forma es regional. |
| RN-07 | Línea evolutiva de cada forma. |
| RN-10 | Tipos de cada forma por generación, tabla de eficacias por generación y métodos de evolución por juego. |
| RN-11 | Grupos huevo de cada especie, para saber si la línea se puede criar. Marcas de legendario y singular, como comprobación. |
| RN-12 | Tipos de cada forma en el juego objetivo y tipos que existen en su generación. |
| RN-13 | Tipos con su orden (primario y secundario) en el juego objetivo. Identificar a Dragonite. |
| RN-14 | Identificar las evoluciones de Eevee (rama de la cadena de Eevee). |
| RN-15 | Método de cada paso de evolución en el juego objetivo, clasificado como tedioso o no. Qué mecánicas tiene cada juego (p. ej., ciclo de día y noche), para saber si una evolución se puede hacer en él. Movimientos que se aprenden subiendo de nivel, para el método «conocer un movimiento». |
| RN-16 | *Hall of Fame*: juego, orden en el recorrido y miembros (forma). Generación de cada juego. Líneas evolutivas, con las excepciones de Dragonite y Eevee. |
| RN-17 | Combates clave de cada juego con sus Pokémon rivales (forma). Tipos de esos Pokémon y tabla de eficacias del juego. |

## Entidades

### Datos de referencia (ingesta)

Generación
:   Número, tipos que existen en ella (p. ej., 15 en la 1.ª: sin Siniestro, Acero ni Hada) y
    tabla de eficacias de tipos (multiplicador de cada tipo atacante contra cada tipo
    defensor).

Juego
:   Identificador, nombre en español, generación de lanzamiento y orden de lanzamiento. Lista
    de Pokémon (por forma) que pueden estar en él (RN-03). Mecánicas que condicionan las
    evoluciones, como el ciclo de día y noche (RN-15).

Especie
:   Número de la Pokédex nacional, nombre, grupos huevo, legendario (sí/no), singular (sí/no)
    y cadena evolutiva a la que pertenece.

Forma (Pokémon)
:   Especie, si es la forma base o una regional (y de qué región), nombre completo
    («Vulpix de Alola») y tipos por generación con su orden: primario y, si lo hay,
    secundario.

Paso de evolución
:   Forma de origen, forma de destino y, para cada juego, el método o métodos con sus
    condiciones: nivel, objeto, intercambio, amistad, hora del día, lugar, movimiento
    conocido, Pokémon o tipo en el equipo, etc. De cada método se deriva si es tedioso
    (RN-15). Con los pasos se reconstruyen las líneas y sus ramas (RN-07, RN-09, RN-14, RN-16).

Movimientos por nivel
:   Para cada forma y juego, los movimientos que aprende subiendo de nivel. Solo se necesitan
    para clasificar las evoluciones que requieren conocer un movimiento (RN-15).

Combate clave
:   Juego, categoría (líder de gimnasio o equivalente, Alto Mando, Campeón, jefe del equipo
    malvado, rival), nombre del entrenador, orden dentro del juego y Pokémon rivales (forma y,
    opcionalmente, nivel). Si el equipo del rival depende del inicial elegido, se guarda cada
    variante (RN-17, [CA-24](../01-ddf/cuestiones-abiertas.md#resueltas)).

### Datos del usuario

Favorito
:   Forma concreta (RN-02, RN-05, RN-09).

Configuración de reglas
:   Para cada regla configurable, si está activa y, si es blanda, su peso (RF-06, RF-07).

Registro del *Hall of Fame*
:   Juego, fecha, orden en el recorrido, notas y miembros (forma). Los tipos de cada miembro
    se obtienen de su forma y la generación del juego (RF-12, RN-16).

## Fuentes previstas

| Dato | Fuente principal | Observaciones |
|------|------------------|---------------|
| Especies, formas, grupos huevo, legendario y singular | PokeAPI | Campos `egg_groups`, `is_legendary` e `is_mythical` de la especie. El grupo «Desconocido» (`no-eggs`) indica que no se puede criar; en las líneas con bebés (Pichu) cuenta el grupo de las demás especies. |
| Tipos actuales y antiguos | PokeAPI | `types` y `past_types` de cada Pokémon. |
| Tabla de eficacias por generación | PokeAPI | `damage_relations` y `past_damage_relations` de cada tipo. |
| Cadenas y métodos de evolución | PokeAPI | `evolution_details` describe las condiciones e incluye `version_group`, el grupo de versiones desde el que se aplica cada método (p. ej., Feebas: belleza en Rubí y Zafiro, intercambio con Escama Bella en Negro y Blanco). Hay que definir cómo se interpreta: un método vale desde su grupo de versiones hasta que otro lo sustituye. Faltan mecánicas de juego, como el ciclo de día y noche, que se cargan como datos inferidos. |
| Movimientos por nivel | PokeAPI | `moves` de cada Pokémon, por grupo de versiones y método de aprendizaje. |
| Pokémon que existen en cada juego | PokeAPI, completado con WikiDex | Las Pokédex regionales de cada grupo de versiones están en PokeAPI. `game_indices` no sirve (p. ej., Crobat no figura en Escarlata y Violeta, y las formas de Hisui no tienen ninguno). Hasta la 7.ª generación se puede deducir de la Pokédex Nacional; desde la 8.ª hay que sumar Pokédex regionales, contenidos descargables y Pokémon que solo llegan por HOME. Lo que no sea seguro se carga como inferido (RN-18). |
| Combates clave | WikiDex | PokeAPI no tiene entrenadores. Las páginas de WikiDex tienen los equipos en plantillas `{{Equipo}}` (Pokémon, tipos, nivel y movimientos) bajo una sección por juego, que se pueden procesar con mwparserfromhell. La lista de entrenadores de cada juego se mantiene a mano. Lo que no se pueda procesar con certeza (revanchas, variantes según el inicial) se carga como inferido (RN-18). |

Con el catálogo actual, ninguna regla necesita datos de Pokémon Showdown (learnsets
competitivos, habilidades o formatos). Si se confirma, se puede aplazar esa fuente con un ADR.

## Origen de los datos

Cada dato que interviene en la generación guarda su origen ([RN-18](../01-ddf/reglas-negocio.md#rn-18)):

| Origen | Significado | Ejemplos |
|--------|-------------|----------|
| Automático | Cargado sin ambigüedad. | Tipos, tabla de eficacias, grupos huevo, métodos de evolución con `version_group`. |
| Inferido | Propuesta de la ingesta, sin certeza. | Llegada antes de completar el juego (por la Pokédex regional), ciclo de día y noche, equipos de los combates clave con variantes. |
| Pendiente | Sin propuesta. | Lo que la ingesta no ha podido deducir. |
| Confirmado | Revisado por el usuario ([RF-15](../01-ddf/requisitos-funcionales.md#rf-15)). | Cualquier dato inferido o pendiente, tras la revisión. |

La confirmación se guarda aparte de los datos cargados, junto con el valor propuesto que se
confirmó. Si una nueva carga propone un valor distinto, la confirmación deja de valer y se
vuelve a pedir. El motor (`core/`) recibe los datos ya resueltos y no conoce su origen.

## Restricciones de llegada por juego

Para [RN-03](../01-ddf/reglas-negocio.md#rn-03) no basta con que un Pokémon exista en el juego:
la etapa que nace del huevo tiene que poder llegar y evolucionar **antes de completarlo**
([CA-28](../01-ddf/cuestiones-abiertas.md#abiertas)). Hay juegos con restricciones hasta que se
obtiene la Pokédex Nacional, que suele darse tras la Liga. Hay que investigarlo juego a juego y
guardarlo como dato de cada juego.

### Rojo Fuego y Verde Hoja (comprobado)

- Antes de la Pokédex Nacional solo se pueden intercambiar Pokémon de la Pokédex de Kanto
  (los 151 de la 1.ª generación). Un Pichu no se puede enviar a Verde Hoja hasta tener la
  Pokédex Nacional, aunque sí después de evolucionarlo a Pikachu.
- No se puede intercambiar con Rubí, Zafiro o Esmeralda hasta tener la Pokédex Nacional y
  completar la misión de Celio en Isla Prima. Antes de la Liga, el equipo solo puede venir de
  otra copia de Rojo Fuego o Verde Hoja.
- Antes de la Pokédex Nacional, los Pokémon intentan evolucionar a especies de la 2.ª
  generación, pero fallan (p. ej., Golbat → Crobat). Por extensión, tampoco funcionan
  Onix → Steelix, Chansey → Blissey, Scyther → Scizor, Seadra → Kingdra, Slowpoke → Slowking,
  Poliwhirl → Politoed, Gloom → Bellossom, Porygon → Porygon2 ni Eevee → Espeon o Umbreon.
- La guardería está en Isla Cuatro, a la que se llega tras la Liga. La crianza se hace en otra
  partida ya completada.
- Conclusión: en Rojo Fuego y Verde Hoja solo pueden ser candidatos los Pokémon de la Pokédex
  de Kanto cuya etapa que nace del huevo también está en ella, y con evoluciones solo dentro de
  ella. Raichu queda fuera, porque su huevo da Pichu.

Fuentes: [Thonky: intercambiar entre Rojo Fuego y Verde Hoja](https://www.thonky.com/pokemon/trade-from-firered-to-leafgreen),
[Bulbapedia: discusión sobre Rojo Fuego y Verde Hoja](https://bulbapedia.bulbagarden.net/wiki/Talk:Pok%C3%A9mon_FireRed_and_LeafGreen_Versions)
y [Bulbapedia: Pokédex Nacional](https://bulbapedia.bulbagarden.net/wiki/National_Pok%C3%A9dex).

### Pendiente de investigar

- Rubí, Zafiro y Esmeralda: si antes de la Pokédex Nacional se pueden recibir Pokémon de fuera
  de la Pokédex de Hoenn y si pueden evolucionar.
- Oro, Plata y Cristal: si hay alguna restricción parecida (en principio, no).
- 4.ª generación en adelante: restricciones de intercambio o evolución antes de la Pokédex
  Nacional, y canales de transferencia disponibles (Pal Park, Pokétransfer, Pokémon HOME), que
  suelen exigir haber completado el juego de destino.

## Comprobación de las fuentes

Consultas puntuales hechas el 2026-10-03 para valorar la viabilidad:

- PokeAPI devuelve `egg_groups` (`no-eggs` para Unown y Pichu, `ditto` para Ditto,
  `indeterminate` para Rotom, que sí se puede criar con Ditto) e `is_baby`.
- `past_types` (Clefairy era Normal hasta la 5.ª generación) y `past_damage_relations`
  (Acero, con cambios hasta la 5.ª) cubren RN-10.
- `evolution_details` incluye `version_group` (Feebas, Magneton).
- Los movimientos por nivel vienen por grupo de versiones. Los de nivel 1 de una evolución
  solo se aprenden con el recordador ([CA-32](../01-ddf/cuestiones-abiertas.md#abiertas)).
- WikiDex responde a la API MediaWiki (`action=parse&prop=wikitext`) y la página de Brock tiene
  su equipo de Rojo Fuego y Verde Hoja en una plantilla `{{Equipo}}`.
