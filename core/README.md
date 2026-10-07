# core/

**Qué es**: el dominio puro de la aplicación: las reglas de negocio (`RN-XX`) y el motor de
generación de equipos, a partir de un `GameContext` inmutable.

**Por qué existe**: aísla las reglas de la red, la base de datos y las bibliotecas de terceros,
para probarlas a fondo con hypothesis ([ADR-0002](../docs/03-adr/0002-monolito-modular-nucleo-puro.md)).

**Contenido** (el detalle, en el *docstring* de cada módulo):

| Ruta | Qué es |
|------|--------|
| `domain/` | Modelos inmutables (`GameContext`, `PokemonData`, `TypeChart`, `KeyBattle`…) y líneas especiales. |
| `rules/catalog.py` | Catálogo de las reglas (`CATALOG`) y configuración del usuario (`RuleSettings`). |
| `rules/candidate.py` | Filtros por candidato. |
| `rules/team.py` | Restricciones entre miembros y reglas de presencia. |
| `rules/soft.py` | Reglas blandas. |
| `rules/check.py` | Comprobación de un equipo elegido en el resultado. |
| `engine/` | `generate(ctx)`: búsqueda, resultado, sugerencias y agrupación de empates. |
| `scoring.py` | Puntuación ponderada, desglose y desempate. |
| `evolution.py` | Si un paso de evolución es tedioso, aleatorio o imposible en el juego. |
| `breeding.py` | Crianza: si una línea se puede criar y qué etapa nace del huevo. |
| `review.py` | Qué datos sin verificar intervienen en una generación. |
| `journey.py` | Qué excluye el recorrido del *Hall of Fame*. |

**Más información**: diseño en [motor de reglas](../docs/02-ddt/motor.md) y
[algoritmo de generación](../docs/02-ddt/algoritmo-generacion.md); dependencias permitidas en la
[arquitectura](../docs/02-ddt/arquitectura.md#reglas-de-dependencia).
