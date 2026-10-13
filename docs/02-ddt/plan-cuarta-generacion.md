# Plan de la 4.ª generación

Plan para cargar la 4.ª generación y que sus juegos puedan ser juego objetivo
([CA-94](../01-ddf/cuestiones-abiertas.md#resueltas),
[RF-11](../01-ddf/requisitos-funcionales.md#rf-11), [RF-05](../01-ddf/requisitos-funcionales.md#rf-05)).
Lo pendiente de cada fase está en su PR; al terminar, este plan se archiva en el
[historial](../06-historial/index.md).

## Alcance

**Dentro**:

| Bloque | Requisitos y decisiones |
|--------|-------------------------|
| Los movimientos que se aprenden por nivel y la regla de CA-32 en el motor | RN-15, CA-32, CA-45 |
| La carga de las especies hasta #0493 y de Diamante, Perla, Platino, HeartGold y SoulSilver, con su Pokédex, apariciones, eventos, iniciales y portadas | CA-94, RF-11, RN-22 a RN-26 |
| Las transferencias de la 4.ª generación y el Parque Compi | RN-25 |
| Diamante, Perla y Platino, y HeartGold y SoulSilver, como juego objetivo: mecánicas, regla de llegada y combates clave | RF-05, RN-03, RN-15, RN-17, CA-28, CA-88, CA-89, CA-95, CA-96 |

**Fuera**: las formas alternativas (Rotom, Giratina, Shaymin, Wormadam), porque solo se carga la
forma por defecto ([CA-11](../01-ddf/cuestiones-abiertas.md#resueltas)); la 5.ª generación en
adelante; y los spin-offs, como Pokémon Ranger, que no cuentan para obtener un Pokémon
([CA-73](../01-ddf/cuestiones-abiertas.md#resueltas)).

## Principios

- **Ampliar sin romper**: los juegos de la 3.ª generación siguen igual; las comprobaciones de la
  carga añaden casos de la 4.ª sin perder los anteriores.
- **Cada fase deja la aplicación usable**: los juegos de la 4.ª se cargan primero sin ser
  completos (sirven para el *Hall of Fame* y la Pokédex) y pasan a ser juego objetivo cuando
  tienen todos sus datos.
- **Comprobado en el código de los juegos**: las restricciones de llegada se investigan en las
  decompilaciones de [pret](https://github.com/pret), como en
  [#8](https://github.com/AlbertoMercado/pokemon-team-builder/issues/8).

## Comprobaciones previas

Hechas el 2026-10-13 con el volcado CSV de PokeAPI del commit fijado (`bc92d3b`):

| Comprobación | Resultado |
|--------------|-----------|
| Especies | 107 nuevas: 493 en total. |
| Juegos | `diamond`, `pearl`, `platinum`, `heartgold` y `soulsilver`, ya en el [catálogo de juegos](datos-curados.md#catalogyaml) con el motivo «su generación todavía no se carga». |
| Evoluciones por movimiento | 7: Mamoswine, Tangrowth y Yanmega (Poder Pasado), Ambipom (Doble Golpe), Lickilicky (Desenrollar), y Mr. Mime y Sudowoodo desde Mime Jr. y Bonsly (Mimético). Bloqueaban la carga (`missing_level_moves`, [CA-45](../01-ddf/cuestiones-abiertas.md#resueltas)). |
| Bebés nuevos | Budew, Chingling, Bonsly, Mime Jr., Happiny, Munchlax y Mantyke nacen con incienso ([CA-36](../01-ddf/cuestiones-abiertas.md#resueltas)); Riolu, sin él. |
| Disparadores y condiciones de evolución | Todos están en el [catálogo de métodos](datos-curados.md#evolution_methodsyaml): aparecen el lugar (Magnezone, Probopass, Leafeon, Glaceon), el sexo (Gallade, Froslass), el objeto equipado de noche (Gliscor, Weavile) y el Pokémon en el equipo (Mantine). |
| Métodos de aparición nuevos | `headbutt`, `honey-tree` (árboles de miel) y `pokemon-ranger` (spin-off): hay que clasificarlos para RN-26. |

## Diseño

### Movimientos por nivel (fase 2)

- Tabla `level_move` ([modelo de datos](modelo-datos.md)), solo con los movimientos que exige
  alguna evolución (`known_move`), por forma y grupo de versiones, con su nivel.
- `core/evolution.py`: un paso con una condición `unless_learnt_by_level` no es tedioso si el
  Pokémon que evoluciona aprende el movimiento por nivel a partir del nivel 2 en el juego
  objetivo ([CA-32](../01-ddf/cuestiones-abiertas.md#resueltas)); la API pasa esos movimientos al
  contexto.
- Desaparece el bloqueo `missing_level_moves`: los movimientos por nivel se cargan siempre.

### Carga de la 4.ª generación (fase 3)

- `ingest/scope.py`: `MAX_GENERATION = 4` y `TARGET_GENERATIONS = {3, 4}`.
- Datos curados: bebés de incienso nuevos (`breeding.yaml`), iniciales (`starters.yaml`), Pokédex
  de cada juego (`pokedex.yaml`, la Nacional en los cinco, como dice
  [CA-70](../01-ddf/cuestiones-abiertas.md#resueltas)), transferencias (`transfers.yaml`: la 4.ª
  entre sí y el Parque Compi desde la 3.ª), Pokémon de evento (`events.yaml`), nombres en
  español de los lugares que falten (`locations.yaml`) y portadas (`covers.yaml`).
- `core/pokedex/encounters.py`: clase de los métodos nuevos (RN-26).
- Comprobaciones de la carga: cantidades, casos conocidos de la 4.ª y que los juegos de la 3.ª
  sigan igual.

### Juegos objetivo (fases 4 y 5)

Para cada grupo (Diamante, Perla y Platino; HeartGold y SoulSilver):

- Mecánicas (`games.yaml`): ciclo de día y noche y concursos. HeartGold y SoulSilver no tienen
  concursos, así que Feebas no puede evolucionar allí.
- Regla de llegada (`arrival.yaml`), investigada en el código de los juegos ([#114](https://github.com/AlbertoMercado/pokemon-team-builder/issues/114)).
- Combates clave (`key_battles/*.yaml`): los 8 líderes, el Alto Mando, el Campeón, el último
  combate obligatorio del jefe malvado (Helio en Sinnoh, Atlas en Johto,
  [CA-95](../01-ddf/cuestiones-abiertas.md#resueltas)) y del rival (Israel en Sinnoh, Plata en
  Johto), sin Kanto en HeartGold y SoulSilver
  ([CA-96](../01-ddf/cuestiones-abiertas.md#resueltas)). Platino tiene sus propios equipos.

## Fases

| Fase | Rama | Qué | Documentación |
|------|------|-----|---------------|
| 1 | `docs/cuarta-generacion` | CA-94 a CA-96, RF-11, RN-17 y RN-25 en el DDF, y este plan. | DDF y este plan |
| 2 | `feat/movimientos-por-nivel` | Tabla `level_move`, la regla de CA-32 en el motor y el bloqueo ajustado. | Modelo de datos, diseño de la carga, motor, Operación de la ingesta |
| 3 | `feat/carga-cuarta-generacion` | El alcance, los datos curados, los métodos de aparición nuevos y las comprobaciones. | Datos curados, diseño de la carga, Operación de la ingesta, motor, CHANGELOG |
| 4 | `feat/sinnoh-objetivo` | Diamante, Perla y Platino como juego objetivo. | Datos requeridos (llegada), datos curados, CHANGELOG |
| 5 | `feat/hgss-objetivo` | HeartGold y SoulSilver como juego objetivo. | Ídem |
| 6 | `chore/release-…` | Versión. | CHANGELOG |

Cada fase que cambia los datos pide repetir la carga, y el CHANGELOG lo avisa.
