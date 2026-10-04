# ingest/

**Qué es**: la CLI de carga de datos (`uv run python -m ingest ...`), pendiente de implementar.

**Por qué existe**: los datos de referencia vienen de fuentes externas y se cargan de forma
puntual, no en cada arranque (RF-11).

**Qué hace**: extrae PokeAPI (volcado CSV), WikiDex (con caché y límite de peticiones) y los
datos curados, los valida y normaliza, y construye `reference.sqlite`
([arquitectura](../docs/02-ddt/arquitectura.md#ingest-carga-de-datos)).

**Restricciones**: solo puede importar `db/` (`lint-imports`).

Más detalle en [Estructura del código](../docs/02-ddt/estructura-codigo.md).
