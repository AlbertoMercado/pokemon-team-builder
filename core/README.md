# core/

**Qué es**: el dominio puro de la aplicación, en Python.

**Por qué existe**: aísla las reglas de negocio (`RN-XX` del DDF) de la red, la base de datos y
cualquier biblioteca de terceros, para poder probarlas a fondo con hypothesis
([ADR-0002](../docs/03-adr/0002-monolito-modular-nucleo-puro.md)).

**Qué hace**: implementa las reglas y el motor de generación de equipos a partir de un
`GameContext` inmutable ([algoritmo](../docs/02-ddt/algoritmo-generacion.md)).

**Restricciones**: solo biblioteca estándar y ningún otro paquete del proyecto. Lo comprueban
`lint-imports` y `tests/test_architecture.py`.

Más detalle en [Estructura del código](../docs/02-ddt/estructura-codigo.md).
