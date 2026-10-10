# tests/

**Qué es**: los tests de Python (pytest + hypothesis).

**Por qué existe**: cada regla de negocio y cada propiedad del motor se verifica de forma
automática ([estrategia de pruebas](../docs/02-ddt/arquitectura.md#estrategia-de-pruebas)).

**Contenido** (qué prueba cada fichero, en su *docstring*):

| Ruta | Qué es |
|------|--------|
| `core/` | Tests del motor. `builders.py` y `scenario.py` son los datos de prueba (ver abajo). |
| `core/pokedex/` | Tests de la Pokédex. `builders.py` y `core/pokedex_scenario.py` son sus datos de prueba (ver abajo). |
| `db/` | Esquemas de `reference.sqlite` y `user.sqlite` (migraciones incluidas). |
| `ingest/` | Carga, fuentes, imágenes y portadas, sobre extractos reales. |
| `api/` | Endpoints con el `TestClient` de FastAPI sobre un directorio de datos temporal (`conftest.py`); `factories.py` crea los `reference.sqlite` de prueba y `scenario.py` escribe el escenario de Rojo Fuego. |
| `docs/` | La referencia de la API generada para la documentación, y que el contrato OpenAPI esté completo (ADR-0012). |
| `e2e/serve.py` | No es un test: arranca la API con la web compilada sobre el escenario de Rojo Fuego para las pruebas de Playwright de `web/e2e/` (`uv run python -m tests.e2e.serve [--port N]`). |
| `test_architecture.py` | Guardián de pureza: `core/` solo importa la biblioteca estándar. |
| `test_network_blocked.py` | Ningún cliente HTTP llega a la red. |
| `conftest.py` | Hace fallar cualquier petición HTTP. |

## Convenciones

- **Sin red**: `conftest.py` bloquea toda petición HTTP. Los datos externos son **extractos
  reales** guardados en `tests/<paquete>/fixtures/`, cada uno con un `README.md` que dice de dónde
  sale y el script que lo regenera. Las imágenes reales no se guardan en git: los tests crean las
  suyas.
- **Reglas de negocio**: el test que verifica una regla lleva `@pytest.mark.rn("RN-XX")` y la cita
  en su nombre o *docstring*.
- **Datos de prueba legibles**: `core/builders.py` tiene constructores
  (`pokemon("gengar", ("ghost", "poison"), line=("gastly", "haunter"))`, `type_chart(...)`,
  `candidate(...)`, `battle(...)`, `context(...)`) en los que cada test solo indica lo que le
  importa. Sin `chain`, cada línea tiene su propia cadena de evolución, para que RN-07 no
  relacione Pokémon que no tienen nada que ver.
- **Escenario real**: `core/scenario.py` construye el contexto de Rojo Fuego desde
  `core/fixtures/firered.json`, un extracto de un `reference.sqlite` real (los Pokémon que pueden
  llegar al juego, la tabla de tipos de la 3.ª generación y los 13 combates clave).
  `core/pokedex_scenario.py` construye la Pokédex de Rojo Fuego desde
  `core/fixtures/pokedex_firered.json` (sus 386 especies con sus apariciones y evoluciones, y los
  juegos que pueden enviarle Pokémon). En la Pokédex, `core/pokedex/builders.py`
  (`pokedex(species("pichu"), species("pikachu", evolves_from="pichu"))`) hace de constructor.
- **Nombres únicos**: los ficheros de test no tienen `__init__.py`, así que su nombre no se puede
  repetir en otro directorio (por eso `test_pokedex_scenario_firered.py`).
- **Imports**: pytest añade la raíz del repositorio al `sys.path` (`pythonpath` en
  `pyproject.toml`) y los tests importan módulos de prueba como `tests.core.builders`.
