# Cuestiones funcionales

Registro de las decisiones funcionales (**CA-XX**) tomadas al redactar el DDF. Cuando surge una
duda nueva, se añade como **abierta**. Al resolverla, se actualizan los requisitos y las reglas
afectados y se anota la decisión.

## Abiertas

Cada cuestión abierta incluye una propuesta, que es la que reflejan provisionalmente las reglas
afectadas.

| ID | Cuestión | Afecta a | Propuesta |
|----|----------|----------|-----------|
| CA-28 | ¿Qué Pokémon pueden llegar al juego objetivo y evolucionar antes de completarlo? | RN-03, RN-14, RN-15, RF-11 | Solo son candidatos los Pokémon cuya etapa de entrada (la que nace del huevo) se puede recibir en el juego objetivo y evolucionar hasta la evolución de favoritos antes de completarlo. Estos datos se cargan como inferidos y los confirma el usuario (RN-18), así que no bloquean la implementación. Investigar cada juego sirve para que las propuestas sean correctas. Ver [lo comprobado en Rojo Fuego y Verde Hoja](../02-ddt/datos-requeridos.md#restricciones-de-llegada-por-juego). |
| CA-32 | ¿Es tediosa una evolución que exige conocer un movimiento que la evolución anterior solo aprende a nivel 1, de modo que hay que usar el recordador de movimientos? | RN-15 | Sí. Aunque las fuentes lo registren como aprendizaje por nivel, en la práctica hay que enseñárselo con el recordador. |
| CA-33 | Si la puntuación solo depende de los tipos, Pokémon con los mismos tipos son intercambiables y los empates se multiplican. ¿Cómo se muestran? | RN-04, RF-08 | Agrupar los equipos empatados que solo se diferencian en miembros con los mismos tipos (p. ej., «Agua: Vaporeon o Lapras»), en lugar de listar cada combinación. |

## Aplazadas

Dependen de la planificación de la ingesta, que queda fuera del alcance de esta versión del
DDF.

| ID | Cuestión | Afecta a | Cuándo se decide |
|----|----------|----------|------------------|
| CA-11 | Qué generaciones y juegos incluye la carga inicial. Los juegos objetivo empiezan en la 2.ª generación (CA-29), aunque se necesitan datos de especies de la 1.ª. | RF-05, RF-11 | Al planificar la ingesta de datos. |

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
| CA-05 | Escala de los pesos de las reglas blandas y valores por defecto. | Pesos enteros de 0 a 10. Por defecto: RN-17 = 10, RN-15 = 3 y RN-06 = 1 (RN-04). |
| CA-10 | ¿Qué reglas forman el catálogo de la primera versión y de qué tipo es cada una? | Un catálogo estático: las reglas RN-01 a RN-10 y las nuevas RN-11 a RN-17. El usuario solo las activa o desactiva y ajusta los pesos de las blandas; los parámetros (Dragonite, Eevee…) son fijos. |
| CA-12 | ¿Qué Pokémon «existen» en una generación? | Los que aparecen en alguno de sus juegos. El filtro es doble: primero por generación y después por el juego, aunque el Pokémon no se pueda atrapar en él (RN-03). |
| CA-13 | ¿Qué otras formas cuentan como Pokémon distintos? | Ninguna aparte de las regionales. Las formas que cambian de forma dinámica en el juego (megaevolución, Gigamax, Rotom, Deoxys…) no se tienen en cuenta (RN-05). |
| CA-14 | ¿Vulpix y Vulpix de Alola cuentan como la misma especie? | Sí, pero no se descartan: tener varias formas de la misma especie solo resta puntuación, con un peso pequeño (RN-06). |
| CA-15 | ¿Qué tipos se usan si cambian entre generaciones? | Los del juego objetivo, incluida su tabla de eficacias (RN-10). |
| CA-16 | ¿Cómo se combinan varios favoritos de la misma línea evolutiva, por ejemplo Vaporeon y Jolteon, o Rhydon y Rhyperior? | Con RN-07 activa, nunca van juntos. Con RN-07 desactivada, RN-12 impide los que comparten tipo (Rhydon y Rhyperior) y RN-14 permite una sola evolución de Eevee. |
| CA-17 | ¿Qué juegos quedan afectados por un equipo ya usado? | Lo marca el recorrido: se excluyen los miembros del equipo del último juego completado, sea de la generación que sea, y los de todos los juegos completados de la misma generación que el juego objetivo. Dragonite nunca queda excluido (RN-16). |
| CA-18 | ¿Qué se excluye de un Pokémon ya usado? | Su línea evolutiva, en la misma forma, no solo esa evolución concreta. Las líneas de Dragonite y Eevee son excepciones (CA-21, RN-16). |
| CA-19 | ¿Tienen prioridad las reglas de presencia o el equipo de 6? | Las reglas de presencia. Antes que un equipo de 6 sin Dragonite o sin evolución de Eevee, se muestra un equipo incompleto que las incluye, con sugerencias (RN-08, RN-13, RN-14). |
| CA-20 | ¿Qué evoluciones son tediosas? | Intercambio, características de concurso (belleza), lugar concreto, pasos, comparación de estadísticas, hora del día, llevar ciertos Pokémon en el equipo y movimientos que el Pokémon no aprende subiendo de nivel. También las que no se pueden hacer en el juego objetivo, como Espeon y Umbreon en Rojo Fuego. La amistad y las piedras u otros objetos no lo son (RN-15). |
| CA-21 | ¿Qué se excluye en las líneas de Dragonite y de Eevee? | La línea de Dragonite nunca se excluye. De la de Eevee solo se excluye la evolución usada: Eevee y el resto de evoluciones siguen siendo candidatos, porque RN-14 exige siempre una (RN-16). |
| CA-22 | ¿Qué Pokémon se descartan por ser legendarios o singulares? | Todos los que no se pueden obtener por crianza: legendarios, singulares, ultraentes, paradójicos y otros, como Ditto o Unown (RN-11). |
| CA-23 | ¿Tienen que estar Dragonite y las evoluciones de Eevee en favoritos? | Sí, y tienen que estar en el equipo aunque eso impida completarlo. En ese caso se muestra el equipo incompleto con sugerencias (RN-08, RN-13, RN-14). Para los tipos del equipo cuenta la evolución de Eevee elegida, no Eevee. |
| CA-24 | ¿Cómo se puntúa la eficacia frente a los combates clave? | Solo por tipos, sin movimientos ni niveles. Ataque: algún miembro es superefectivo contra el rival. Defensa: algún miembro resiste al menos un tipo del rival y no es débil a ninguno. Cada combate pesa lo mismo. Cuentan los líderes de gimnasio o sus equivalentes, el Alto Mando, el Campeón y los jefes del equipo malvado (RN-17). |
| CA-25 | ¿Con qué etapa de su línea llega cada Pokémon al juego objetivo? | Con la que nace del huevo. Si esa etapa no puede llegar al juego objetivo, el Pokémon no es candidato (RN-03, CA-28). Las evoluciones que revisa RN-15 son las que van desde esa etapa. |
| CA-26 | ¿Cuentan los combates contra el rival como combates clave? | Solo su equipo en el último combate obligatorio, sin el Pokémon inicial, que depende de la elección del jugador. Si el rival es también el Campeón, ese combate cuenta una vez (RN-17). |
| CA-27 | ¿Cómo empieza el equipo cada juego? | Se cría en otro juego y llega al juego objetivo por transferencia, en su etapa inicial y a nivel 1 (o al más bajo posible). Se recoge en el primer PC y se juega con él desde ahí. Por eso no importa dónde se atrapa cada Pokémon (RN-03, RN-11). |
| CA-29 | ¿Qué juegos pueden ser juego objetivo? | Solo los que permiten la crianza. Se excluyen los de la 1.ª generación (Rojo, Azul y Amarillo), porque no se puede llevar a ellos un Pokémon recién nacido del huevo (RF-05). |
| CA-30 | ¿Qué se hace con los datos que no se pueden cargar de forma fiable? | Se cargan como inferidos (con propuesta) o pendientes, y el usuario tiene que confirmarlos antes de generar un equipo. Los datos confirmados son responsabilidad del usuario: si son erróneos, el resultado puede ser inexacto, pero no es un error del algoritmo (RN-18, RF-15). |
| CA-31 | ¿Qué se hace con las sugerencias que dependen de datos sin confirmar? | Se muestran marcadas como «sin verificar». No se pide confirmarlas (RN-08, RN-18). |
