# tests/

**Qué es**: los tests de Python (pytest + hypothesis).

**Por qué existe**: cada regla de negocio y cada propiedad del motor se verifica de forma
automática ([estrategia de pruebas](../docs/02-ddt/arquitectura.md#estrategia-de-pruebas)).

**Qué contiene**:

- `test_architecture.py`: comprueba que `core/` solo importa la biblioteca estándar.
- `core/`: tests del motor de reglas. `core/builders.py` tiene constructores de datos de prueba
  legibles (`pokemon(...)`, `type_chart(...)`, `context(...)`) que usan todos sus tests.
  `core/scenario.py` construye el escenario real de Rojo Fuego a partir de un extracto de
  `reference.sqlite` (`core/fixtures/`, con su README y el script que lo genera).
- `api/`: tests de la API con el `TestClient` de FastAPI sobre un directorio de datos temporal
  (`api/conftest.py`). `api/factories.py` crea los `reference.sqlite` de prueba.
- `db/test_user_schema.py`: esquema de `user.sqlite` (las migraciones coinciden con los modelos,
  se pueden deshacer y las restricciones funcionan).
- `test_network_blocked.py`: comprueba que ningún cliente HTTP llega a la red.
- `db/test_reference_schema.py`: esquema de `reference.sqlite` (tablas documentadas, lectura
  y escritura, y restricciones de integridad).
- `ingest/test_load.py`: carga de `reference.sqlite` (filas desordenadas, registro de la
  carga, recuento por origen, conservación de la base de datos anterior si algo falla) y CLI.
- `ingest/test_pokeapi.py`: fuente de PokeAPI sobre un extracto real del volcado
  (`ingest/fixtures/pokeapi/`, con su README y el script que lo genera).
- `ingest/test_curated.py`: datos curados (los ficheros reales, los esquemas y la fuente).
- `ingest/test_wikidex.py`: fuente de WikiDex sobre páginas reales recortadas
  (`ingest/fixtures/wikidex/`, con su README, su atribución y el script que las genera).
- `conftest.py`: hace fallar cualquier petición HTTP. **Los tests nunca usan la red.**
- Los tests de cada paquete van en `tests/<paquete>/` (`core/`, `db/`, `ingest/`, `api/`).

pytest importa los paquetes desde la raíz del repositorio (`pythonpath` en `pyproject.toml`).

Los tests que verifican una regla llevan `@pytest.mark.rn("RN-XX")` y la citan en su nombre o
*docstring*.

Más detalle en [Estructura del código](../docs/02-ddt/estructura-codigo.md).
