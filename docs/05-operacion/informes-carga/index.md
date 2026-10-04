# Informes de carga

Historial de las cargas de `reference.sqlite` que importan: las **bloqueadas**, que necesitan
que el arquitecto revise el modelo, y las **completadas** que cierran un bloqueo o estrenan un
commit de PokeAPI o unos juegos ([ADR-0008](../../03-adr/0008-cargas-bloqueadas.md)).

La CLI de ingesta escribe los informes en `data/reports/`, fuera de git. Aquí se registran a
mano, junto con su JSON, siguiendo el
[protocolo de registro](../ingesta.md#protocolo-de-registro).

| Fecha | Estado | Commit de PokeAPI | Bloqueos | Informe | Resolución |
|-------|--------|-------------------|----------|---------|------------|
| — | — | — | — | Aún no hay informes registrados. | — |

Estados:

- **Abierta**: carga bloqueada pendiente de resolver.
- **Resuelta**: carga bloqueada cuyos bloqueos ya resuelve una versión en `main`; enlaza sus
  PR.
- **Completada**: carga sin bloqueos.

Nombre de los ficheros: `AAAA-MM-DD-<bloqueada|completada>-<commit-de-pokeapi>.md` y `.json`.
