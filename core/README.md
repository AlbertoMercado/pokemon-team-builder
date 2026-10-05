# core/

**Qué es**: el dominio puro de la aplicación, en Python.

**Por qué existe**: aísla las reglas de negocio (`RN-XX` del DDF) de la red, la base de datos y
cualquier biblioteca de terceros, para poder probarlas a fondo con hypothesis
([ADR-0002](../docs/03-adr/0002-monolito-modular-nucleo-puro.md)).

**Qué hace**: implementa las reglas y el motor de generación de equipos a partir de un
`GameContext` inmutable ([algoritmo](../docs/02-ddt/algoritmo-generacion.md)).

**Contenido** (fases 1 a 6 de 6 del [plan del motor](../docs/02-ddt/plan-motor.md)):

| Ruta | Qué hace |
|------|----------|
| `domain/` | Modelos inmutables: `TypeChart`, `PokemonData` y sus etapas y pasos de evolución, `Candidate`, `PoolEntry`, `GameInfo`, `KeyBattle`, `HallOfFameEntry` y `GameContext`; y las líneas especiales (`lines.py`). |
| `rules/catalog.py` | Catálogo de las 20 reglas (`CATALOG`) y configuración del usuario (`RuleSettings`). |
| `rules/candidate.py` | Filtros por candidato (RN-03, RN-11, RN-16) con el motivo de cada descarte. |
| `rules/team.py` | Restricciones entre miembros (RN-07, RN-12, RN-14) y reglas de presencia (RN-13, RN-14). |
| `rules/check.py` | `check_team(ctx, miembros)`: comprueba un equipo elegido en el resultado con las mismas reglas que el motor (RF-12, CA-53). |
| `engine/` | `generate(ctx)`: filtros, presencia, búsqueda con retroceso (`search.py`), sugerencias para los huecos (`suggestions.py`), agrupación de empates (`grouping.py`) y resultado (`result.py`). |
| `rules/soft.py` | Reglas blandas (RN-06, RN-15, RN-17, RN-20), cada una con una puntuación entre 0 y 1. |
| `evolution.py` | Si un paso de evolución es tedioso, aleatorio o imposible en el juego. |
| `scoring.py` | Puntuación ponderada, desglose por regla y clave de desempate (RN-04, RN-19); `Scorer` guarda el perfil de cada miembro para puntuar muchos equipos. |
| `breeding.py` | Si una línea se puede criar y qué etapa nace del huevo. |
| `review.py` | Qué datos sin verificar intervienen en una generación y hay que confirmar antes (RN-18). |
| `journey.py` | Qué excluye el recorrido del *Hall of Fame*. |

**Restricciones**: solo biblioteca estándar y ningún otro paquete del proyecto. Lo comprueban
`lint-imports` y `tests/test_architecture.py`.

Detalle de lo implementado en [Motor de reglas](../docs/02-ddt/motor.md) y de la estructura en
[Estructura del código](../docs/02-ddt/estructura-codigo.md).
