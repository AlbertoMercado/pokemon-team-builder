# tests/

**Qué es**: los tests de Python (pytest + hypothesis).

**Por qué existe**: cada regla de negocio y cada propiedad del motor se verifica de forma
automática ([estrategia de pruebas](../docs/02-ddt/arquitectura.md#estrategia-de-pruebas)).

**Qué contiene**:

- `test_architecture.py`: comprueba que `core/` solo importa la biblioteca estándar.
- Los tests de cada paquete irán en `tests/<paquete>/` (`core/`, `ingest/`, `api/`).

Los tests que verifican una regla llevan `@pytest.mark.rn("RN-XX")` y la citan en su nombre o
*docstring*.

Más detalle en [Estructura del código](../docs/02-ddt/estructura-codigo.md).
