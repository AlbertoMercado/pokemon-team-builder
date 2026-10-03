# 0006 · Búsqueda exacta con retroceso y fracciones exactas

- **Estado**: Aceptado
- **Fecha**: 2026-10-03
- **Decisores**: Alberto Mercado

## Contexto

El motor elige los mejores equipos de 6 entre los candidatos válidos
([RN-04](../01-ddf/reglas-negocio.md#rn-04)):

- Hay restricciones entre pares de miembros (RN-07, RN-12, RN-14) y reglas de presencia
  (RN-13, RN-14).
- La puntuación no es aditiva por miembro, porque la cobertura de RN-17 depende de la
  combinación.
- Hay que devolver todos los equipos empatados, desempatados con
  [RN-19](../01-ddf/reglas-negocio.md#rn-19), y siempre el mismo resultado para la misma
  entrada ([RF-08](../01-ddf/requisitos-funcionales.md#rf-08)).

La medición con candidatos sintéticos da menos de un segundo con 60 candidatos y RN-12 activa
([algoritmo](../02-ddt/algoritmo-generacion.md#tamano-de-la-busqueda)).

## Decisión

- Usamos una **búsqueda exacta con retroceso** sobre el grafo de incompatibilidades: se fijan
  primero los miembros de las reglas de presencia y se recorren los candidatos en un orden
  canónico.
- Las puntuaciones se calculan con **fracciones exactas** (`fractions.Fraction`). Los equipos
  se comparan por la clave `(puntuación, miembros con dos tipos)`.
- Si con datos reales hiciera falta, se añade **ramificación y poda** con una cota superior de
  la puntuación, sin cambiar el resultado.

Detalle en el [algoritmo de generación](../02-ddt/algoritmo-generacion.md).

## Alternativas consideradas

### Programación lineal entera (p. ej., OR-Tools o PuLP)

- ✅ Escala mejor con muchos candidatos.
- ❌ Dependencia externa en `core/`. Modelar la cobertura de RN-17 y obtener todos los empates
  es más complejo.

### Heurísticas (voraz, búsqueda local, algoritmos genéticos)

- ✅ Muy rápidas.
- ❌ No garantizan el mejor equipo ni todos los empates, y el resultado puede variar.

### Coma flotante

- ✅ Más rápida.
- ❌ Dos equipos empatados pueden diferir en el último decimal y el desempate no se aplicaría.

## Consecuencias

### Positivas

- Resultado exacto y determinista.
- Se puede comparar con fuerza bruta en tests de propiedades con casos pequeños.

### Negativas / riesgos

- El coste crece mucho si RN-12 está desactivada y hay muchos favoritos. Hay que medirlo con
  datos reales.

### Acciones derivadas

- [ ] Medir el rendimiento con los favoritos reales en el primer prototipo.

## Referencias

- [Algoritmo de generación](../02-ddt/algoritmo-generacion.md)
