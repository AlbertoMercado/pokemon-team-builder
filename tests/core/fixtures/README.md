# Extracto de Rojo Fuego para el escenario real del motor

**Qué es**: `firered.json`, un extracto de un `reference.sqlite` real con lo que el motor
necesita para generar equipos en Pokémon Rojo Fuego:

- el juego, sus mecánicas (ninguna: Rojo Fuego no tiene reloj ni concursos) y sus iniciales
  (Venusaur, Charizard y Blastoise);
- los 17 tipos de la 3.ª generación y sus 289 eficacias;
- los 140 Pokémon que pueden llegar al juego antes de completarlo, cada uno con sus tipos en
  la 3.ª generación, sus etapas desde la primera de la línea, los grupos huevo de toda la
  línea, sus pasos de evolución en Rojo Fuego y Verde Hoja y su disponibilidad;
- los 13 combates clave, con los tipos de cada Pokémon rival.

**Por qué existe**: los tests del motor no usan la base de datos
([convenciones de los tests](../../README.md#convenciones)). Con datos reales,
`tests/core/test_scenario_firered.py` comprueba que el resultado es razonable y que la
generación tarda menos de un segundo. `tests/core/scenario.py` lo convierte en un
`GameContext`.

Los valores inferidos o pendientes (como la llegada a Rojo Fuego) se usan tal cual, como si
el usuario hubiera confirmado las propuestas de la carga
([RN-18](../../../docs/01-ddf/reglas-negocio.md#rn-18)).

**Origen**: carga del 2026-10-04 con el commit `bc92d3b` de PokeAPI, los datos curados de Rojo
Fuego y los equipos de WikiDex. El JSON guarda el commit en `source`. De WikiDex solo se
guardan los Pokémon de cada combate y sus tipos, no su contenido.

**Cómo se regenera** (por ejemplo, al cambiar el commit de PokeAPI o los datos curados):

1. Ejecutar una carga real: `uv run python -m ingest`.
2. Generar el extracto:
   `uv run python tests/core/fixtures/extract_firered.py data/reference.sqlite`.
3. Ejecutar `uv run pytest tests/core/test_scenario_firered.py`. Si los equipos esperados
   cambian, revisar que el nuevo resultado tiene sentido y actualizar `EXPECTED_TEAMS`.

# Extracto de la Pokédex de Rojo Fuego

**Qué es**: `pokedex_firered.json`, un extracto de un `reference.sqlite` real con lo que
necesitan las reglas de la Pokédex en Rojo Fuego
([RN-22 a RN-26](../../../docs/01-ddf/reglas-negocio.md#reglas-de-la-pokedex)):

- el juego, sus mecánicas, si tiene crianza y sus iniciales (Bulbasaur, Charmander y Squirtle);
- las 386 especies de la Pokédex Nacional en su orden, cada una con su generación, sus grupos
  huevo, si es un bebé de incienso, los pasos de evolución que llevan a ella en Rojo Fuego, sus
  apariciones y si es de evento;
- los cuatro juegos que pueden enviarle Pokémon (Rubí, Zafiro, Esmeralda y Verde Hoja), con sus
  apariciones y sus iniciales.

Las formas se guardan como su especie (`deoxys-normal` es `deoxys`), porque la Pokédex
registra especies. Cada aparición va en una línea:
`[lugar, zona, método, probabilidad, condiciones, objeto de evento]`.

**Por qué existe**: con datos reales, `tests/core/pokedex/test_pokedex_scenario_firered.py`
comprueba los casos conocidos del [plan de la Pokédex](../../../docs/02-ddt/plan-pokedex.md) y
que la Pokédex entera se calcula en menos de un segundo. `tests/core/pokedex_scenario.py` lo
convierte en un `PokedexContext`.

**Origen**: carga del 2026-10-10 con el commit `bc92d3b` de PokeAPI y los datos curados de la
Pokédex. El JSON guarda el commit en `source`.

**Cómo se regenera**:

1. Ejecutar una carga real: `uv run python -m ingest`.
2. Generar el extracto:
   `uv run python tests/core/fixtures/extract_pokedex_firered.py data/reference.sqlite`.
3. Ejecutar `uv run pytest tests/core/pokedex/`. Si cambia un caso conocido, revisar que el
   nuevo resultado tiene sentido antes de actualizar el test.
