# API

API HTTP de la aplicación, servida por FastAPI bajo el prefijo `/api`. El contrato completo se
publica como OpenAPI en `/api/openapi.json`, del que se genera el cliente del frontend
([ADR-0007](../03-adr/0007-cliente-generado-openapi.md)), y la documentación interactiva en
`/api/docs`. Los endpoints marcados con ✅ están implementados; el resto llega con las fases
del [plan de la API](plan-api.md#fases). Cómo se arranca: [Operación](../05-operacion/api.md).

## Convenciones

- JSON en peticiones y respuestas, con nombres de campo en `snake_case`.
- Los recursos se identifican con las claves naturales del
  [modelo de datos](modelo-datos.md) (`firered`, `vulpix-alola`, `RN-07`).
- Los errores usan el formato por defecto de FastAPI (`{"detail": ...}`) con estos códigos:
    - `404`: el recurso no existe.
    - `409`: la operación no se puede hacer en el estado actual (p. ej., generar con datos sin
      confirmar).
    - `422`: datos de entrada no válidos.
    - `503`: todavía no se han cargado los datos de referencia (`reference.sqlite`).
- Sin autenticación: la aplicación es de un solo usuario.

## Endpoints

### Catálogo

| Método | Ruta | Descripción | Requisitos |
|--------|------|-------------|------------|
| `GET` | `/api/pokemon` | Lista de Pokémon. Filtros: `q` (nombre), `type`, `favorite`. | RF-01 |
| `GET` | `/api/pokemon/{pokemon}` | Ficha: número, nombre, tipos actuales, línea evolutiva y método de cada evolución. | RF-02 |

### Favoritos

| Método | Ruta | Descripción | Requisitos |
|--------|------|-------------|------------|
| `GET` | `/api/favorites` | Lista de favoritos con su número total (`total`), en orden de la Pokédex Nacional. Cada uno con su forma, nombre, número, tipos actuales y cuándo se añadió. ✅ | RF-04 |
| `PUT` | `/api/favorites/{pokemon}` | Añade un favorito y lo devuelve. Es idempotente. `404` si la forma no existe en los datos cargados. ✅ | RF-03 |
| `DELETE` | `/api/favorites/{pokemon}` | Quita un favorito: `204`, o `404` si no lo era. ✅ | RF-03, RF-04 |

Los **tipos actuales** son los de la última generación cargada (hoy, la 3.ª: Clefairy es
Normal). Para generar se usan los del juego objetivo ([RN-10](../01-ddf/reglas-negocio.md#rn-10)).

### Reglas

| Método | Ruta | Descripción | Requisitos |
|--------|------|-------------|------------|
| `GET` | `/api/rules` | Las 20 reglas del catálogo, en orden, con su nombre, descripción, tipo (`hard`, `presence`, `soft` o `mechanism`), si son configurables, si están activas, su peso y su peso por defecto. ✅ | RF-06, RF-07 |
| `PATCH` | `/api/rules/{rule_id}` | Cambia `enabled`, `weight` (0 a 10) o los dos, y devuelve la regla. `404` si no existe; `409` si no es configurable o se da peso a una regla que no es blanda; `422` si el peso está fuera de rango o no se indica nada. ✅ | RF-06, RF-07 |

`user.sqlite` solo guarda las reglas que el usuario ha cambiado; el resto usa los valores por
defecto del catálogo ([CA-41](../01-ddf/cuestiones-abiertas.md#resueltas)).

### Juegos y revisión de datos

| Método | Ruta | Descripción | Requisitos |
|--------|------|-------------|------------|
| `GET` | `/api/games` | Juegos que pueden ser juego objetivo: los marcados como objetivo y con crianza, en orden de lanzamiento. ✅ | RF-05 |
| `GET` | `/api/games/{game}/review` | Datos sin verificar que intervienen, con su propuesta y estado. | RF-15 |
| `PUT` | `/api/games/{game}/review/{fact_key}` | Confirma un dato, con el valor propuesto o corregido: un booleano, o la lista de Pokémon del equipo si es un combate clave. | RF-15 |
| `POST` | `/api/games/{game}/review/accept-proposals` | Acepta de una vez todas las propuestas inferidas. Los datos pendientes, sin propuesta, se siguen tratando uno a uno. | RF-15 |

### Generación

| Método | Ruta | Descripción | Requisitos |
|--------|------|-------------|------------|
| `POST` | `/api/games/{game}/generations` | Genera los equipos con los favoritos, las reglas y las confirmaciones actuales. `409` con la lista de datos pendientes si queda alguno sin confirmar. | RF-08, RF-09, RF-10 |

!!! note "Esquema provisional"
    Este ejemplo es anterior al motor y a [CA-51](../01-ddf/cuestiones-abiertas.md#resueltas).
    El esquema definitivo, con los grupos, los huecos y las puntuaciones enteras, se fija en la
    fase 4 del [plan de la API](plan-api.md#fases).

La generación no se guarda: es un cálculo sin estado. Ejemplo de respuesta, abreviado (solo 3
de los 6 miembros):

```json
{
  "status": "complete",
  "score": "18.5",
  "groups": [
    {
      "members": [
        {"options": ["dragonite"]},
        {"options": ["jolteon"]},
        {"options": ["lapras", "cloyster"]}
      ],
      "breakdown": [
        {"rule_id": "RN-17", "weight": 10, "score": "0.95", "contribution": "9.5"},
        {"rule_id": "RN-20", "weight": 5, "score": "1", "contribution": "5"},
        {"rule_id": "RN-15", "weight": 3, "score": "1", "contribution": "3"},
        {"rule_id": "RN-06", "weight": 1, "score": "1", "contribution": "1"}
      ],
      "dual_type_members": 3
    }
  ],
  "discards": [
    {"pokemon": "raichu", "rule_id": "RN-03", "reason": "arrival", "fact_key": "pokemon:firered:raichu:arrival"}
  ],
  "unmet_presence_rules": [],
  "suggestions": [],
  "confirmed_facts_used": ["pokemon:firered:raichu:arrival"],
  "data_version": {"pokeapi_commit": "…", "ingested_at": "…"}
}
```

- Las puntuaciones se envían como **enteros redondeados**; las aportaciones se reparten con el
  método del mayor resto para que sigan sumando el total
  ([CA-51](../01-ddf/cuestiones-abiertas.md#resueltas)). El motor decide el orden y los empates
  con fracciones exactas ([ADR-0006](../03-adr/0006-algoritmo-busqueda-exacta.md)).
- `groups` agrupa los equipos empatados por miembros intercambiables
  ([RN-04](../01-ddf/reglas-negocio.md#rn-04)), ya desempatados con
  [RN-19](../01-ddf/reglas-negocio.md#rn-19).
- Si `status` es `incomplete`, `suggestions` incluye cada hueco con la regla de presencia que
  lo reserva, si la hay, y sus Pokémon ordenados, cada uno con `verified`
  ([RN-08](../01-ddf/reglas-negocio.md#rn-08), [RN-18](../01-ddf/reglas-negocio.md#rn-18)).

### Hall of Fame

| Método | Ruta | Descripción | Requisitos |
|--------|------|-------------|------------|
| `GET` | `/api/hall-of-fame` | Registros en el orden del recorrido. Filtro: `game`. | RF-13 |
| `POST` | `/api/hall-of-fame` | Registra un equipo (juego, fecha, notas y hasta 6 Pokémon). Guarda los tipos de cada miembro en ese juego. | RF-12 |
| `PATCH` | `/api/hall-of-fame/{id}` | Corrige un registro. | RF-13 |
| `DELETE` | `/api/hall-of-fame/{id}` | Elimina un registro. | RF-13 |

### Metadatos

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/meta` | Versión de la aplicación y de los datos: commit de PokeAPI, fecha de la carga y juegos cargados. `data` es nulo si la carga no dejó registro. ✅ |
