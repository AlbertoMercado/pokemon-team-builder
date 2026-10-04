# 0005 · Datos curados en YAML versionado

- **Estado**: Aceptado
- **Fecha**: 2026-10-03
- **Decisores**: Alberto Mercado

## Contexto

Algunos datos no están en ninguna fuente o no se pueden deducir con certeza
([RN-18](../01-ddf/reglas-negocio.md#rn-18)):

- La lista de combates clave de cada juego, con la página de WikiDex de cada entrenador.
- Las mecánicas de cada juego, como el ciclo de día y noche.
- Las restricciones de llegada antes de completar el juego
  ([CA-28](../01-ddf/cuestiones-abiertas.md#abiertas)).
- Correcciones puntuales a datos de las fuentes.

Estos datos los mantiene una persona y conviene poder revisarlos y saber cuándo cambiaron.

## Decisión

Guardamos los datos curados en **ficheros YAML dentro del repositorio** (`data/curated/`),
validados con pydantic en la ingesta. Cada valor indica su origen: `inferred` si es una
propuesta o `automatic` si es seguro. Los cambios entran por PR, como el código.

## Alternativas consideradas

### Tablas editables en la base de datos

- ✅ Se podrían editar desde la aplicación.
- ❌ Se perderían al reconstruir `reference.sqlite` y no tendrían historial ni revisión.

### Hojas de cálculo

- ✅ Cómodas de editar.
- ❌ Difíciles de validar y de revisar en un PR.

## Consecuencias

### Positivas

- Historial y revisión de los datos curados con Git.
- La validación con pydantic detecta errores antes de cargar.

### Negativas / riesgos

- Mantenerlos es trabajo manual, sobre todo los combates clave de cada juego.

### Acciones derivadas

- [x] Definir los esquemas de los ficheros YAML ([datos curados](../02-ddt/datos-curados.md)).
- [ ] Rellenar los datos de Rojo Fuego y Verde Hoja para el primer prototipo: mecánicas,
  llegada y lista de combates clave hechos; faltan los equipos de los combates (fase 5).

## Referencias

- [Datos requeridos por las reglas](../02-ddt/datos-requeridos.md)
- [Datos curados](../02-ddt/datos-curados.md)
