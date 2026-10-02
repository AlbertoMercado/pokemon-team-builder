# Cuestiones funcionales

Registro de las decisiones funcionales (**CA-XX**) tomadas al redactar el DDF. Cuando surge una
duda nueva, se añade como **abierta**. Al resolverla, se actualizan los requisitos y las reglas
afectados y se anota la decisión.

## Abiertas

No hay cuestiones abiertas.

## Aplazadas

Dependen del diseño de las reglas de elección o de la planificación de la ingesta, que quedan
fuera del alcance de esta versión del DDF.

| ID | Cuestión | Afecta a | Cuándo se decide |
|----|----------|----------|------------------|
| CA-05 | Escala de los pesos de las reglas blandas. | RF-07, RN-04 | Al diseñar las reglas de elección. |
| CA-10 | Qué reglas forman el catálogo de la primera versión y de qué tipo es cada una. | RN-XX | Al diseñar las reglas de elección. |
| CA-11 | Qué generaciones y juegos incluye la carga inicial (2 o 3 primeras generaciones, ver CA-02). | RF-05, RF-11 | Al planificar la ingesta de datos. |
| CA-16 | Cómo se combinan varios favoritos de la misma línea evolutiva, por ejemplo Vaporeon y Jolteon, o Rhydon y Rhyperior. | RN-07, RN-09 | Al diseñar las reglas de elección. |

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
| CA-12 | ¿Qué Pokémon «existen» en una generación? | Los que aparecen en alguno de sus juegos. El filtro es doble: primero por generación y después por el juego, aunque el Pokémon no se pueda atrapar en él (RN-03). |
| CA-13 | ¿Qué otras formas cuentan como Pokémon distintos? | Ninguna aparte de las regionales. Las formas que cambian de forma dinámica en el juego (megaevolución, Gigamax, Rotom, Deoxys…) no se tienen en cuenta (RN-05). |
| CA-14 | ¿Vulpix y Vulpix de Alola cuentan como la misma especie? | Sí, pero no se descartan: tener varias formas de la misma especie solo resta puntuación, con un peso pequeño (RN-06). |
| CA-15 | ¿Qué tipos se usan si cambian entre generaciones? | Los del juego objetivo, incluida su tabla de eficacias (RN-10). |
