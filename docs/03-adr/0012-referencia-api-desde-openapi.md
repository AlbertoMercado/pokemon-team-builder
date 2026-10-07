# 0012 · Referencia de la API generada desde OpenAPI con un hook de MkDocs

- **Estado**: Aceptado
- **Fecha**: 2026-10-07
- **Decisores**: Alberto Mercado

## Contexto

La API estaba descrita en cinco sitios: el DDT (tabla de endpoints, ejemplos JSON y tablas de
campos), Operación, el manual, `api/README.md` y el propio código, cuyas descripciones
(`Field(description=...)` y los *docstrings* de los endpoints) forman el contrato OpenAPI del que
se genera el cliente de la web ([ADR-0007](0007-cliente-generado-openapi.md)). Cada cambio de la
API había que repetirlo a mano, y las copias ya se habían desincronizado: los ejemplos del DDT
no tenían `image_url`, `cover_url` ni `cover_source_url` (#76).

La documentación tiene que tener una sola fuente por tema
([cómo se documenta](../02-ddt/documentacion.md)). Para la referencia de la API (endpoints,
parámetros, respuestas y campos), esa fuente es el código: el usuario eligió publicar el contrato
OpenAPI en MkDocs.

## Decisión

- **La referencia de la API se genera del contrato OpenAPI al construir la documentación**, con
  un *hook* de MkDocs propio (`docs/hooks/api_reference.py`). El *hook* crea la página
  [Referencia de la API](../02-ddt/api-referencia.md), en español, con cada endpoint (resumen,
  descripción, parámetros, cuerpo y respuestas) y cada esquema (sus campos, tipos y
  descripciones). La página no se escribe en disco ni se versiona.
- **El código es la fuente**: el *docstring* de cada endpoint dice qué hace y sus errores, y cada
  campo y parámetro lleva su `description`. Un test (`tests/docs/test_api_reference.py`) falla si
  falta alguna, y la CI construye la documentación con `--strict`.
- **El DDT de la API** se queda con las convenciones y las decisiones de diseño, y el manual con
  cómo se usa; los dos enlazan a la referencia en lugar de repetirla.

## Alternativas consideradas

### neoteroi-mkdocs (plugin OAD)

- ✅ Genera la referencia sin código propio.
- ❌ Sus etiquetas están en inglés («Description», «Input parameters», avisos de ejemplos
  generados) y no se pueden traducir; la documentación es en español.
- ❌ Muestra los campos como esquemas JSON en bruto, no como tablas con sus descripciones.
- ❌ Una dependencia más, con sus extensiones.

### Swagger UI incrustado (mkdocs-swagger-ui-tag)

- ✅ Interfaz interactiva conocida.
- ❌ Se dibuja en el navegador: no entra en la búsqueda de la documentación ni sigue su estilo.
- ❌ La API ya sirve la misma interfaz en `/api/docs` cuando está arrancada.

### Mantener la referencia a mano en el DDT

- ✅ Sin código ni dependencias.
- ❌ Es lo que se había desincronizado: cada cambio de la API hay que copiarlo a mano.

## Consecuencias

### Positivas

- La referencia no puede desincronizarse del código: se genera de él en cada construcción.
- Un cambio de la API se documenta una vez, en su código; el contrato completo es además mejor
  para el cliente generado y para `/api/docs`.
- Sin dependencias nuevas: los *hooks* son parte de MkDocs.

### Negativas / riesgos

- Un *hook* propio que mantener (unas 200 líneas), con sus tests. Si el formato de OpenAPI de
  FastAPI cambia, puede haber que ajustarlo.
- Construir la documentación importa la API (`api.main`): el job de documentación necesita las
  dependencias del proyecto, que ya instala.
- Los ejemplos JSON del DDT desaparecen: la referencia muestra los esquemas, no ejemplos.

### Acciones derivadas

- [x] *Hook*, página generada, descripciones completas en el código y test de completitud.
- [x] Reducir el DDT de la API a convenciones y decisiones, y que el manual enlace a la referencia.

## Referencias

- [Hooks de MkDocs](https://www.mkdocs.org/user-guide/configuration/#hooks).
- #76, [ADR-0007](0007-cliente-generado-openapi.md).
