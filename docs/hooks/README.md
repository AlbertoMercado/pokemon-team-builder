# docs/hooks/

**Qué es**: los [*hooks*](https://www.mkdocs.org/user-guide/configuration/#hooks) de MkDocs del
proyecto: código que se ejecuta al construir la documentación. No son páginas (`exclude_docs`
en `mkdocs.yml`).

**Por qué existe**: lo que se genera del código se publica sin copiarlo a mano
([cómo se documenta](../02-ddt/documentacion.md)).

**Contenido**:

| Ruta | Qué es |
|------|--------|
| `api_reference.py` | Genera la [referencia de la API](../02-ddt/api-referencia.md) del contrato OpenAPI ([ADR-0012](../03-adr/0012-referencia-api-desde-openapi.md)). Sus tests, en `tests/docs/`. |
