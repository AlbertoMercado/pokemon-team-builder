# 0002 · Monolito modular con núcleo puro

- **Estado**: Aceptado
- **Fecha**: 2026-10-03
- **Decisores**: Alberto Mercado

## Contexto

La aplicación es personal, de un solo usuario y se ejecuta en local. Trabaja con datos de
referencia de solo lectura y con pocos datos del usuario. La generación de equipos tarda menos
de un segundo ([algoritmo](../02-ddt/algoritmo-generacion.md#tamano-de-la-busqueda)).

La lógica de negocio (19 reglas `RN-XX`) es la parte más delicada y tiene que poder probarse a
fondo, incluso con tests basados en propiedades.

## Decisión

Usamos un **monolito modular**: un solo proceso con paquetes separados (`core/`, `db/`,
`ingest/`, `api/` y `web/`). El dominio queda aislado al estilo **hexagonal** (puertos y
adaptadores):

- `core/` es puro: no accede a la red, a la base de datos ni al sistema de ficheros, y solo
  depende de la biblioteca estándar.
- Las dependencias van en un solo sentido: `api → core, db` e `ingest → db`. `core/` no
  depende de nada.
- Las reglas son componentes de un catálogo estático, con una interfaz por clase de regla.

Detalle en la [arquitectura](../02-ddt/arquitectura.md).

## Alternativas consideradas

### Microservicios (ingesta, motor y API por separado)

- ✅ Despliegue y escalado independientes.
- ❌ Complejidad de red, despliegue y observabilidad sin ninguna necesidad que la justifique.

### Monolito por capas sin aislar el dominio

- ✅ Menos código de traducción entre capas.
- ❌ Las reglas acabarían mezcladas con SQLModel y FastAPI, y no se podrían probar con
  hypothesis sin base de datos.

## Consecuencias

### Positivas

- Las reglas se prueban sin infraestructura.
- Un solo proceso que desplegar y depurar.
- Cambiar de base de datos o de framework web no afecta al dominio.

### Negativas / riesgos

- Hay que traducir entre los modelos de `db/` y los de `core/`.
- Las reglas de dependencia no se cumplen solas: hay que comprobarlas en CI.

### Acciones derivadas

- [x] Añadir `import-linter` a las dependencias de desarrollo y a CI con los contratos de
  dependencia ([estructura del código](../02-ddt/estructura-codigo.md#reglas-de-dependencia)).
- [x] Añadir `db` a los paquetes que revisa mypy en `pyproject.toml`.

## Referencias

- [Arquitectura](../02-ddt/arquitectura.md)
- [Estructura del código](../02-ddt/estructura-codigo.md)
- [import-linter](https://import-linter.readthedocs.io/)
