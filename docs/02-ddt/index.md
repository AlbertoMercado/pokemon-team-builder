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
- [Diseño de la carga de datos](carga-datos.md): qué se carga y cómo se interpretan PokeAPI y
  WikiDex, y las comprobaciones de la carga.
- [Diseño de la web](web.md): pantallas, rutas, endpoints que usan y cómo se muestran los
  errores.

Los planes de implementación ya ejecutados están en el [historial](../06-historial/index.md).

## Decisiones

Las decisiones de arquitectura están en el [registro de ADR](../03-adr/index.md).
