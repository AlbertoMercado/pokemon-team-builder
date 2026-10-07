# Documento de Diseño Técnico (DDT)

Describe **cómo** se implementa lo que define el [DDF](../01-ddf/index.md). Las decisiones de
arquitectura se registran como [ADR](../03-adr/index.md).

## Contenido

- [Arquitectura](arquitectura.md): componentes, reglas de dependencia, flujos, despliegue y
  estrategia de pruebas.
- [Motor de reglas](motor.md): lo implementado en `core/`: modelos del dominio, reglas,
  puntuación, generación de equipos, revisión de datos y comprobación de un equipo elegido.
- [Estructura del código](estructura-codigo.md): qué es y qué hace cada directorio y contratos
  de dependencia entre paquetes.
- [Cómo se documenta](documentacion.md): la fuente única de cada tema (mapa de fuentes) y qué
  se documenta en cada PR.
- [Modelo de datos](modelo-datos.md): las dos bases de datos SQLite, los datos revisables y el
  contexto del motor.
- [API](api.md): convenciones y decisiones de diseño de la API.
- [Referencia de la API](api-referencia.md): endpoints, parámetros, respuestas y campos,
  generada del contrato OpenAPI.
- [Algoritmo de generación](algoritmo-generacion.md): forma del problema, búsqueda, tamaño y
  empates.
- [Datos requeridos por las reglas](datos-requeridos.md): qué datos necesita cada regla, de qué
  fuente salen, su origen y las restricciones de llegada por juego.
- [Datos curados](datos-curados.md): los ficheros YAML de `data/curated/`, su esquema y cómo se
  cargan.
- [Plan de implementación de la web](plan-web.md): alcance, principios, pantallas y rutas,
  estructura de `web/`, fases, pruebas y CI.
- [Plan de las imágenes de los Pokémon](plan-imagenes.md): obtenerlas en la ingesta,
  servirlas desde la API y mostrarlas en la web (RF-17), con sus comprobaciones previas, fases y
  riesgos.
- [Plan de las portadas de los juegos](plan-portadas.md): obtenerlas de WikiDex en la ingesta,
  servirlas desde la API y mostrarlas en la web (RF-18), con la fuente de cada combate clave.
- [Plan de implementación de la API](plan-api.md): alcance, `user.sqlite`, construcción del
  contexto, datos revisables, fases y estrategia de pruebas.
- [Plan de implementación del motor](plan-motor.md): alcance, interfaz, módulos, cómo se
  interpreta cada regla, pruebas, fases y trazabilidad de las reglas de `core/`.
- [Plan de la primera carga de datos](plan-carga-datos.md): alcance (generaciones 1 a 3),
  revisión del volcado de PokeAPI, datos curados, WikiDex y fases de implementación.

## Decisiones

Las decisiones de arquitectura están en el [registro de ADR](../03-adr/index.md).
