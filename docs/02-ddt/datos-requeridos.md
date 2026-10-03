# Datos requeridos por las reglas

!!! warning "Borrador"
    Se deriva del catálogo de reglas del [DDF](../01-ddf/reglas-negocio.md) (RN-01 a RN-17) y
    sirve de base para el modelo de datos. Todavía no es el modelo definitivo: no fija tablas,
    claves ni tipos.

## Resumen por regla

| Regla | Datos que necesita |
|-------|--------------------|
| RN-02, RN-09 | Favoritos del usuario (forma concreta). Cadena evolutiva para conocer las preevoluciones. |
| RN-03 | Generación de cada juego. Pokémon (por forma) que pueden estar en cada juego, también por transferencia. Etapa con la que llega cada línea ([CA-25](../01-ddf/cuestiones-abiertas.md#abiertas)). |
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
| Cadenas y métodos de evolución | PokeAPI, completado con WikiDex | `evolution_details` describe las condiciones, pero no siempre indica en qué juego se aplica cada método (p. ej., Milotic o Magnezone). Hay que comprobarlo en la prueba de datos. |
| Movimientos por nivel | PokeAPI | `moves` de cada Pokémon, por grupo de versiones y método de aprendizaje. |
| Pokémon que existen en cada juego | PokeAPI, completado con WikiDex | Las Pokédex regionales no incluyen todo lo que se puede conseguir por intercambio o evolución. Es el dato más delicado de RN-03. |
| Combates clave | WikiDex | PokeAPI no tiene entrenadores. Es la principal razón para usar WikiDex. |

Con el catálogo actual, ninguna regla necesita datos de Pokémon Showdown (learnsets
competitivos, habilidades o formatos). Si se confirma, se puede aplazar esa fuente con un ADR.
