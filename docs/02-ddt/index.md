# Documento de Diseño Técnico (DDT)

Describe **cómo** se implementa lo que define el [DDF](../01-ddf/index.md). Las decisiones de
arquitectura se registran como [ADR](../03-adr/index.md).

## Contenido

- [Arquitectura](arquitectura.md): componentes, reglas de dependencia, flujos, despliegue y
  estrategia de pruebas.
- [Estructura del código](estructura-codigo.md): qué es y qué hace cada directorio, contratos
  de dependencia entre paquetes y cómo se documenta el código.
- [Modelo de datos](modelo-datos.md): las dos bases de datos SQLite, los datos revisables y el
  contexto del motor.
- [API](api.md): endpoints HTTP y formato de la generación.
- [Algoritmo de generación](algoritmo-generacion.md): forma del problema, búsqueda, tamaño y
  empates.
- [Datos requeridos por las reglas](datos-requeridos.md): qué datos necesita cada regla, de qué
  fuente salen, su origen y las restricciones de llegada por juego.
- [Datos curados](datos-curados.md): los ficheros YAML de `data/curated/`, su esquema y cómo se
  cargan.
- [Plan de implementación del motor](plan-motor.md): alcance, interfaz, módulos, cómo se
  interpreta cada regla, pruebas, fases y trazabilidad de las reglas de `core/`.
- [Plan de la primera carga de datos](plan-carga-datos.md): alcance (generaciones 1 a 3),
  revisión del volcado de PokeAPI, datos curados, WikiDex y fases de implementación.

## Decisiones

| ADR | Decisión |
|-----|----------|
| [0001](../03-adr/0001-stack-tecnologico.md) | Stack tecnológico |
| [0002](../03-adr/0002-monolito-modular-nucleo-puro.md) | Monolito modular con núcleo puro |
| [0003](../03-adr/0003-dos-bases-de-datos-sqlite.md) | Dos bases de datos SQLite: referencia y usuario |
| [0004](../03-adr/0004-pokeapi-volcado-csv.md) | PokeAPI mediante su volcado CSV, y Showdown aplazado |
| [0005](../03-adr/0005-datos-curados-yaml.md) | Datos curados en YAML versionado |
| [0006](../03-adr/0006-algoritmo-busqueda-exacta.md) | Búsqueda exacta con retroceso y fracciones exactas |
| [0007](../03-adr/0007-cliente-generado-openapi.md) | Cliente del frontend generado desde OpenAPI |
