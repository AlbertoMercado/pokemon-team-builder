# 0013 · Formas de obtener los Pokémon: apariciones de PokeAPI y datos curados

- **Estado**: Aceptado
- **Fecha**: 2026-10-07
- **Decisores**: Alberto Mercado

## Contexto

La Pokédex ([RF-20](../01-ddf/requisitos-funcionales.md#rf-20) a
[RF-24](../01-ddf/requisitos-funcionales.md#rf-24)) propone la forma más sencilla de obtener cada
Pokémon en un juego superado ([RN-24](../01-ddf/reglas-negocio.md#rn-24) a
[RN-26](../01-ddf/reglas-negocio.md#rn-26)). Necesita, para los 11 juegos cargados:

- dónde aparece cada Pokémon salvaje, con qué método (andar, surfear, cañas…) y con qué
  probabilidad;
- los regalos, los intercambios con PNJ, los Pokémon estáticos y los errantes;
- los fósiles, los regalos que dependen del inicial y los Pokémon que solo se obtienen por evento
  o desde spin-offs;
- qué juegos pueden transferir Pokémon a cuáles;
- la Pokédex de cada juego.

WikiDex tiene las localizaciones de cada Pokémon y las rutas con sus porcentajes, pero en texto
libre de MediaWiki que habría que interpretar página a página. PokeAPI, que ya usamos mediante su
volcado CSV de un commit fijado ([ADR-0004](0004-pokeapi-volcado-csv.md)), tiene las apariciones
en tablas (`encounters.csv`, `encounter_slots.csv`, `encounter_methods.csv`,
`location_areas.csv`) y las Pokédex (`pokedexes.csv`, `pokemon_dex_numbers.csv`).

Comprobado el 2026-10-07 en el commit fijado ([plan](../02-ddt/plan-pokedex.md#comprobaciones-previas)):
PokeAPI cubre los 11 juegos, con regalos, intercambios, estáticos y errantes, pero no tiene los
nombres en español de los lugares de Kanto y Johto, no distingue los fósiles de los regalos y no
tiene los Pokémon de evento ni la compatibilidad entre juegos.

## Decisión

- **Las apariciones y las Pokédex salen de PokeAPI**, del mismo volcado CSV y commit fijado que
  el resto ([CA-72](../01-ddf/cuestiones-abiertas.md#resueltas)).
- **Lo que PokeAPI no tiene va en datos curados** ([ADR-0005](0005-datos-curados-yaml.md),
  [CA-78](../01-ddf/cuestiones-abiertas.md#resueltas)): la compatibilidad de transferencias, qué
  Pokédex usa cada juego, los Pokémon de evento y los que solo se obtienen en spin-offs, los
  fósiles, los regalos que dependen del inicial y los nombres en español de los lugares que
  faltan.
- **La ingesta sigue sin WikiDex para esto.** WikiDex solo se usaría para juegos que PokeAPI no
  cubra (Diamante Brillante y Perla Reluciente, Leyendas: Arceus, Escarlata y Púrpura), cuando se
  carguen.

## Alternativas consideradas

### WikiDex (localizaciones y artículos de cada ruta)

- ✅ En español y con los nombres que usa el jugador.
- ✅ Cubre todos los juegos.
- ❌ Texto libre: plantillas distintas por generación y por página, frágil de interpretar.
- ❌ Cientos de páginas por juego, a una petición por segundo.

### PokeAPI y datos curados (elegida)

- ✅ Datos estructurados, con probabilidad por zona y método.
- ✅ Reproducible: el mismo commit fijado y la misma caché que el resto de la carga.
- ✅ Los casos que PokeAPI no tiene son pocos y estables, y se revisan en git.
- ❌ Faltan los nombres en español de Kanto y Johto: hay que traducirlos una vez.
- ❌ No cubre los juegos más recientes de Switch.

## Consecuencias

### Positivas

- La forma de obtener cada Pokémon se calcula sin red, como el resto de las reglas.
- Los datos curados nuevos siguen el mismo proceso que los existentes: validados al cargar,
  revisados por PR.

### Negativas / riesgos

- Los errores de PokeAPI en apariciones antiguas pasarían a la ficha. La opción de ver otras
  formas de obtención ([RF-23](../01-ddf/requisitos-funcionales.md#rf-23)) sirve también para
  detectarlos.
- Para los juegos de Switch hará falta otra fuente cuando se carguen.

### Acciones derivadas

- [ ] Cargar las Pokédex, las apariciones y los datos curados nuevos (#94).

## Referencias

- [Plan de la Pokédex](../02-ddt/plan-pokedex.md)
- [PokeAPI: volcado CSV](https://github.com/PokeAPI/pokeapi/tree/master/data/v2/csv)
- Issue #94
