# tests/

**Qué es**: los tests de Python (pytest + hypothesis).

**Por qué existe**: cada regla de negocio y cada propiedad del motor se verifica de forma
automática ([estrategia de pruebas](../docs/02-ddt/arquitectura.md#estrategia-de-pruebas)).

**Qué contiene**:

- `test_architecture.py`: comprueba que `core/` solo importa la biblioteca estándar.
- `db/test_reference_schema.py`: esquema de `reference.sqlite` (tablas documentadas, lectura
  y escritura, y restricciones de integridad).
- `ingest/test_load.py`: carga de `reference.sqlite` (filas desordenadas, registro de la
  carga, recuento por origen, conservación de la base de datos anterior si algo falla) y CLI.
- `ingest/test_pokeapi.py`: fuente de PokeAPI sobre un extracto real del volcado
  (`ingest/fixtures/pokeapi/`, con su README y el script que lo genera).
- `ingest/test_curated.py`: datos curados (los ficheros reales, los esquemas y la fuente).
- `conftest.py`: hace fallar cualquier petición HTTP. **Los tests nunca usan la red.**
- Los tests de cada paquete van en `tests/<paquete>/` (`core/`, `db/`, `ingest/`, `api/`).

pytest importa los paquetes desde la raíz del repositorio (`pythonpath` en `pyproject.toml`).

Los tests que verifican una regla llevan `@pytest.mark.rn("RN-XX")` y la citan en su nombre o
*docstring*.

Más detalle en [Estructura del código](../docs/02-ddt/estructura-codigo.md).
