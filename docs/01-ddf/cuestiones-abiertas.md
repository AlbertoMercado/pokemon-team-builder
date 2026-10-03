# Cuestiones funcionales

Registro de las decisiones funcionales (**CA-XX**) tomadas al redactar el DDF. Cuando surge una
duda nueva, se añade como **abierta**. Al resolverla, se actualizan los requisitos y las reglas
afectados y se anota la decisión.

## Abiertas

Cada cuestión abierta incluye una propuesta, que es la que reflejan provisionalmente las reglas
afectadas.

| ID | Cuestión | Afecta a | Propuesta |
|----|----------|----------|-----------|
| CA-05 | Escala de los pesos de las reglas blandas y valores por defecto. | RF-07, RN-04 | Pesos enteros de 0 a 10. Por defecto: RN-17 = 10, RN-15 = 3 y RN-06 = 1. |
| CA-21 | En las líneas que se ramifican (Eevee, Oddish, Poliwag, Slowpoke, Ralts…), ¿qué excluye RN-16? | RN-16 | Solo la rama del Pokémon usado: sus preevoluciones y sus evoluciones posteriores, no las ramas hermanas. Si se excluyera toda la línea, usar Vaporeon en un juego descartaría todas las evoluciones de Eevee en el siguiente, y RN-14 no se podría cumplir con favoritos. |
| CA-22 | ¿Qué Pokémon cuentan como legendarios o singulares? | RN-11 | La clasificación oficial que recogen las fuentes (PokeAPI: `is_legendary` e `is_mythical`). Los ultraentes y los Pokémon paradójicos no cuentan. |
| CA-23 | ¿Tienen que estar Dragonite y las evoluciones de Eevee en favoritos para cumplir RN-13 y RN-14? | RN-02, RN-13, RN-14 | Sí. Si Dragonite no está en favoritos, se pasa al siguiente nivel de RN-13 (tipo primario Dragón). Si ningún favorito cumple la regla, se reserva un hueco con sugerencias (RN-08). |
| CA-24 | ¿Cómo se puntúa la eficacia frente a los combates clave? ¿Qué combates cuentan? | RN-17, RF-11 | Solo por tipos (ataque y defensa), sin movimientos ni niveles. Cada combate pesa lo mismo. Cuentan los líderes de gimnasio o sus equivalentes (pruebas de Alola), el Alto Mando, el Campeón y los combates obligatorios contra el jefe del equipo malvado. Queda por decidir si cuenta el rival. |

## Aplazadas

Dependen de la planificación de la ingesta, que queda fuera del alcance de esta versión del
DDF.

| ID | Cuestión | Afecta a | Cuándo se decide |
|----|----------|----------|------------------|
| CA-11 | Qué generaciones y juegos incluye la carga inicial (2 o 3 primeras generaciones, ver CA-02). | RF-05, RF-11 | Al planificar la ingesta de datos. |

## Resueltas

| ID | Cuestión | Decisión |
|----|----------|----------|
| CA-01 | ¿Una lista de favoritos o varias? | Una única lista. Al elegir el juego, primero se filtra y después se aplica el algoritmo (RN-02, RN-03). |
| CA-02 | ¿Es imprescindible la carga de datos? | Sí (Must), pero se empieza con un conjunto pequeño y controlable, por ejemplo las 2 o 3 primeras generaciones, para validar el algoritmo. El alcance exacto queda en CA-11 (RF-11). |
| CA-03 | ¿Las formas son entradas independientes? | Las formas regionales son Pokémon distintos y se indican con su nombre completo («Marowak de Alola»). El algoritmo nunca deduce una forma a partir de otra (RN-05). Además, cada favorito es la evolución hasta la que se quiere llegar (RN-09). |
| CA-04 | ¿Se permiten especies o líneas evolutivas repetidas? ¿Puede el usuario definir reglas? | Se trabaja con un catálogo de reglas predefinido que el usuario configura (RN-06, RN-07). Que la app reciba reglas definidas por el usuario pasa a deseable (RF-14). |
| CA-06 | ¿Qué pasa si no se puede formar un equipo? | El equipo se completa siempre con favoritos. Si no se llega a 6, se muestra el equipo incompleto con el mayor número de favoritos y se sugieren Pokémon no favoritos que encajen con las reglas (RN-08, RF-10). |
| CA-07 | ¿Qué se guarda de cada miembro en el Hall of Fame? | Nombre y tipo o tipos (RF-12). |
| CA-08 | ¿Qué significa «disponible en el juego»? | Un Pokémon es candidato si existe en el juego, aunque no se pueda atrapar en él. Ver CA-12 (RN-03). |
| CA-09 | ¿Cómo se desempata? | Se recomiendan todos los equipos empatados (RN-04). |
| CA-10 | ¿Qué reglas forman el catálogo de la primera versión y de qué tipo es cada una? | Un catálogo estático: las reglas RN-01 a RN-10 y las nuevas RN-11 a RN-17. El usuario solo las activa o desactiva y ajusta los pesos de las blandas; los parámetros (Dragonite, Eevee…) son fijos. |
| CA-12 | ¿Qué Pokémon «existen» en una generación? | Los que aparecen en alguno de sus juegos. El filtro es doble: primero por generación y después por el juego, aunque el Pokémon no se pueda atrapar en él (RN-03). |
| CA-13 | ¿Qué otras formas cuentan como Pokémon distintos? | Ninguna aparte de las regionales. Las formas que cambian de forma dinámica en el juego (megaevolución, Gigamax, Rotom, Deoxys…) no se tienen en cuenta (RN-05). |
| CA-14 | ¿Vulpix y Vulpix de Alola cuentan como la misma especie? | Sí, pero no se descartan: tener varias formas de la misma especie solo resta puntuación, con un peso pequeño (RN-06). |
| CA-15 | ¿Qué tipos se usan si cambian entre generaciones? | Los del juego objetivo, incluida su tabla de eficacias (RN-10). |
| CA-16 | ¿Cómo se combinan varios favoritos de la misma línea evolutiva, por ejemplo Vaporeon y Jolteon, o Rhydon y Rhyperior? | Con RN-07 activa, nunca van juntos. Con RN-07 desactivada, RN-12 impide los que comparten tipo (Rhydon y Rhyperior) y RN-14 permite una sola evolución de Eevee. |
| CA-17 | ¿Qué juegos quedan afectados por un equipo ya usado? | Lo marca el recorrido: se excluyen los miembros del equipo del último juego completado, sea de la generación que sea, y los de todos los juegos completados de la misma generación que el juego objetivo. Dragonite nunca queda excluido (RN-16). |
| CA-18 | ¿Qué se excluye de un Pokémon ya usado? | Su línea evolutiva, en la misma forma, no solo esa evolución concreta. Las ramas se tratan en CA-21 (RN-16). |
| CA-19 | ¿Tienen prioridad las reglas de presencia o el equipo de 6? | Las reglas de presencia. Antes que un equipo de 6 sin Dragonite o sin evolución de Eevee, se muestra un equipo incompleto que las incluye, con sugerencias (RN-08, RN-13, RN-14). |
| CA-20 | ¿Qué evoluciones son tediosas? | Intercambio, características de concurso (belleza), lugar concreto, pasos, comparación de estadísticas, hora del día, llevar ciertos Pokémon en el equipo y movimientos que el Pokémon no aprende subiendo de nivel. La amistad y las piedras u otros objetos no lo son (RN-15). |
