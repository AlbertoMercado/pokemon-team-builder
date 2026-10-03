# 0004 · PokeAPI mediante su volcado CSV, y Showdown aplazado

- **Estado**: Aceptado
- **Fecha**: 2026-10-03
- **Decisores**: Alberto Mercado

## Contexto

[ADR-0001](0001-stack-tecnologico.md) eligió PokeAPI, Pokémon Showdown y WikiDex como fuentes.
Al concretar los [datos requeridos por las reglas](../02-ddt/datos-requeridos.md) se ha visto
que:

- Cargar desde la API REST de PokeAPI exige miles de peticiones (especies, formas, cadenas de
  evolución, movimientos…), con su límite de uso y su caché.
- El repositorio de PokeAPI publica los mismos datos como CSV (`data/v2/csv`). Incluyen todo lo
  necesario: `pokemon_evolution` con `version_group_id`, `pokemon_egg_groups`,
  `pokemon_types_past`, `type_efficacy_past`, `pokedexes`, `pokemon_moves`, `pokemon_forms` y
  los nombres en español.
- Ninguna regla del catálogo necesita datos de Showdown (movimientos competitivos,
  habilidades o formatos).

## Decisión

- Cargamos PokeAPI a partir de su **volcado CSV, fijado a un commit concreto** del repositorio.
  El commit se guarda en los datos curados y en `ingest_run`. Actualizar los datos es cambiar
  ese commit y volver a ejecutar la ingesta.
- Los identificadores numéricos del CSV se traducen a claves naturales al cargar
  ([ADR-0003](0003-dos-bases-de-datos-sqlite.md)).
- **Aplazamos Pokémon Showdown**: no se usa mientras ninguna regla lo necesite.
- WikiDex se mantiene solo para los equipos de los combates clave.

## Alternativas consideradas

### API REST de PokeAPI

- ✅ Formato JSON más cómodo y siempre actualizado.
- ❌ Miles de peticiones, límites de uso y resultados que cambian entre ejecuciones.

### Descargar el volcado completo de la API (`api-data`)

- ✅ Mismo formato que la API REST, sin peticiones.
- ❌ Muchos más ficheros y más pesados que los CSV, con datos redundantes.

## Consecuencias

### Positivas

- Unas pocas descargas en lugar de miles de peticiones.
- La carga es reproducible: el mismo commit da siempre los mismos datos.
- Una fuente menos que mantener.

### Negativas / riesgos

- El esquema de los CSV puede cambiar entre commits. Al actualizar el commit, la validación
  con pydantic lo detecta.
- Hay que traducir ids numéricos a claves naturales, incluidos los nombres en español
  (`local_language_id` 7).

### Acciones derivadas

- [ ] Elegir el commit inicial de PokeAPI.
- [ ] Revisar las condiciones de uso de los datos de PokeAPI y de WikiDex (CC BY-NC-SA) e
  incluir la atribución en la aplicación.

## Referencias

- [PokeAPI: datos CSV](https://github.com/PokeAPI/pokeapi/tree/master/data/v2/csv)
- [Datos requeridos por las reglas](../02-ddt/datos-requeridos.md)
