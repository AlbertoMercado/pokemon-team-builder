# Extracto de Rojo Fuego para el escenario real del motor

**Qué es**: `firered.json`, un extracto de un `reference.sqlite` real con lo que el motor
necesita para generar equipos en Pokémon Rojo Fuego:

- el juego y sus mecánicas (ninguna: Rojo Fuego no tiene reloj ni concursos);
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
