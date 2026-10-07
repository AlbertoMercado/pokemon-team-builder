# Cómo se documenta

Todo proceso, decisión e implementación queda documentado, **cada cosa en un solo lugar**. El
resto de documentos **enlazan** a ese lugar en vez de repetirlo: una copia acaba
desincronizándose y llevando a errores (#76).

## Principios

- **Una sola fuente por tema**: el [mapa de fuentes](#mapa-de-fuentes) dice cuál es. Si un
  documento necesita ese contenido, enlaza a la sección concreta (con su ancla) y, como mucho,
  dice en una frase de qué trata.
- **Lo que se genera del código no se copia a mano**: la referencia de la API sale de OpenAPI
  ([ADR-0007](../03-adr/0007-cliente-generado-openapi.md)) y cada módulo se explica en su
  *docstring*.
- **El estado no se documenta en páginas de diseño**: qué está hecho y qué falta está en el
  [`CHANGELOG.md`](https://github.com/AlbertoMercado/pokemon-team-builder/blob/main/CHANGELOG.md)
  y en las [issues](https://github.com/AlbertoMercado/pokemon-team-builder/issues). Las páginas
  describen lo que hay; lo pendiente se enlaza a su issue.
- **Lo vigente, separado de lo histórico**: los planes de fase ya ejecutados se archivan como
  historial y no se mantienen; lo que sigue en vigor se pasa a su fuente.
- **Un índice ligero para las sesiones**: [`CLAUDE.md`](https://github.com/AlbertoMercado/pokemon-team-builder/blob/main/CLAUDE.md)
  se carga en cada sesión de Claude Code. Es un índice breve: las reglas imprescindibles en una
  línea y, para cada tema, el enlace a su fuente, para ir directo a la sección que hace falta sin
  leer documentos enteros.

## Mapa de fuentes

| Tema | Fuente única | Quién enlaza |
|------|--------------|--------------|
| Propósito, alcance, forma de jugar y glosario | [DDF](../01-ddf/index.md) | `README.md`, manual |
| Requisitos funcionales (`RF-XX`) | [Requisitos funcionales](../01-ddf/requisitos-funcionales.md) | DDT, issues, PR, CHANGELOG |
| Reglas de negocio (`RN-XX`) | [Reglas de negocio](../01-ddf/reglas-negocio.md) | Motor, tests, issues |
| Cuestiones funcionales (`CA-XX`) | [Cuestiones funcionales](../01-ddf/cuestiones-abiertas.md) | DDF, DDT, ADR |
| Decisiones de arquitectura y su porqué | [ADR](../03-adr/index.md) | DDT, Operación |
| Componentes y reglas de dependencia | [Arquitectura](arquitectura.md) | `CLAUDE.md`, READMEs |
| Qué hace cada fichero de código o de tests | Su *docstring* (o comentario de cabecera en la web) | El `README.md` de su directorio |
| Qué hay en cada directorio | Su `README.md`: un índice, una línea por entrada | [Estructura del código](estructura-codigo.md) |
| Estrategia de pruebas por capa | [Arquitectura](arquitectura.md#estrategia-de-pruebas) | `tests/README.md`, Web |
| Convenciones de los tests (constructores, escenarios, *fixtures*, sin red) | `tests/README.md` | Motor, ingesta |
| Cómo se hacen cumplir las dependencias y cómo añadir un paquete | [Estructura del código](estructura-codigo.md) | `CLAUDE.md` |
| Implementación de las reglas en `core/` | [Motor de reglas](motor.md) | Tests, `core/README.md` |
| Algoritmo de generación | [Algoritmo de generación](algoritmo-generacion.md) | Motor, ADR-0006 |
| Tablas, columnas y migraciones | [Modelo de datos](modelo-datos.md) | Ingesta, API |
| Qué datos necesita cada regla y de dónde salen | [Datos requeridos](datos-requeridos.md) | DDF, ingesta |
| Esquema de `data/curated/*.yaml` | [Datos curados](datos-curados.md) | Ingesta, `data/README.md` |
| Qué se carga y cómo se interpretan las fuentes | [Diseño de la carga](carga-datos.md) | Ingesta, código de `ingest/` |
| Pantallas, rutas y errores de la web | [Diseño de la web](web.md) | Manual, código de `web/` |
| Referencia de la API (endpoints, campos, errores) | El código (*docstrings* y `description`), publicado en la [referencia de la API](api-referencia.md) ([ADR-0012](../03-adr/0012-referencia-api-desde-openapi.md)) | Manual, DDT |
| Convenciones de la API y decisiones de diseño | [API](api.md) | Manual |
| Cómo se usa cada interfaz (CLI, API y web) | [Manual de usuario](../04-manual-usuario/index.md) | `README.md` |
| Cómo funciona la ingesta por dentro | [Ingesta de datos](../05-operacion/ingesta.md) | Manual |
| Comandos de desarrollo y CI | [Comandos y CI](../05-operacion/comandos.md) | `CLAUDE.md`, `README.md` |
| Preparar el entorno | [Entorno de desarrollo](../05-operacion/entorno-desarrollo-macos.md) | `README.md` |
| Numerar y publicar versiones | [Versiones](../05-operacion/versiones.md) | Skill `publicar-version`, `CLAUDE.md` |
| Cambios de cada versión | `CHANGELOG.md` | *Releases* de GitHub |
| Lo pendiente | Issues de GitHub | Páginas que lo mencionan |
| Cómo se planificó cada parte (no vigente) | [Historial](../06-historial/index.md) | ADR |
| Cómo se documenta | Esta página | `CLAUDE.md` |

!!! note "En curso"
    La documentación se está ajustando a este mapa por temas (#76). Hasta terminar, algunos temas
    aún tienen copias en otras páginas.

## El README de un directorio

Un índice breve, sin repetir lo que dice el código ni el diseño:

- **Qué es** y **por qué existe**, en una frase cada uno, con el enlace a su ADR.
- **Contenido**: una línea por subdirectorio o fichero importante. El detalle está en su
  *docstring*.
- **Más información**: los enlaces a la fuente de su diseño (DDT), de su uso (manual) y de cómo se
  opera (Operación).

No lleva estado ni fases (eso está en el `CHANGELOG.md` y las issues), ni las reglas de
dependencia (están en la [arquitectura](arquitectura.md#reglas-de-dependencia)).

## En cada PR

Todo código o cambio de base de datos se documenta **en el mismo PR**, en la fuente de su tema:

- **Módulo, paquete o fichero de tests**: su *docstring* (qué es, por qué existe y qué hace), y
  su línea en el `README.md` del directorio si es una entrada nueva. Un directorio nuevo lleva su
  `README.md` y una fila en la [estructura del código](estructura-codigo.md).
- **Base de datos**: cada tabla, columna o migración, en el [modelo de datos](modelo-datos.md).
- **API**: las descripciones del contrato (`Field(description=...)`, la `description` de cada
  parámetro y el *docstring* de cada endpoint, con sus errores); la
  [referencia](api-referencia.md) se genera sola y un test exige que no falte ninguna. El
  [DDT de la API](api.md), solo si cambia una convención o una decisión.
- **Interfaz de uso** (CLI, API o web): cómo se usa, orientado a tareas, en el
  [manual de usuario](../04-manual-usuario/index.md).
- **Comando nuevo**: en [Comandos y CI](../05-operacion/comandos.md).
- **Decisión de arquitectura**: un ADR a partir de la [plantilla](../03-adr/0000-plantilla.md).
- **Cambio para el usuario**: una línea en **Sin publicar** del `CHANGELOG.md`.

Si el cambio toca un tema cuya fuente es otra página, **se enlaza, no se copia**. Si al
documentar encuentras el mismo contenido en dos sitios, deja la fuente y sustituye el otro por un
enlace.
