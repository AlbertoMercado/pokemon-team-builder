# Diseño de la carga de datos

Qué carga la ingesta y cómo interpreta sus fuentes para construir `reference.sqlite`. Cómo
funciona paso a paso, la caché y el informe: [ingesta de datos](../05-operacion/ingesta.md);
cómo se usa: el [manual](../04-manual-usuario/cargar-datos.md); el esquema de los datos curados:
[datos curados](datos-curados.md).

## Alcance

| Elemento | Qué se carga | Cantidad |
|----------|---------------|----------|
| Especies | 1.ª a 4.ª generación: de #0001 Bulbasaur a #0493 Arceus ([CA-94](../01-ddf/cuestiones-abiertas.md#resueltas)) | 493 (151 + 100 + 135 + 107) |
| Formas (`pokemon`) | Solo la forma por defecto de cada especie | 493 |
| Juegos | Todos los de las generaciones 1 a 4 | 16 juegos en 10 grupos de versiones |
| Juegos objetivo | Los de la 3.ª y la 4.ª generación que están completos ([RF-05](../01-ddf/requisitos-funcionales.md#rf-05)): hoy, los 5 de la 3.ª, Diamante, Perla y Platino | 8 de 10 |
| Tipos | Los que existen hasta la 4.ª generación | 15 en la 1.ª, 17 desde la 2.ª |
| Tabla de eficacias | Una por generación | 4 |
| Combates clave | Los de los 5 juegos objetivo | Unos 30 entrenadores en WikiDex |
| Pokédex | La Nacional y las de Kanto, Johto, Hoenn y Sinnoh, con las especies cargadas | 7 (1714 números) |
| Apariciones | Las de los 16 juegos, en los lugares donde ocurren | Unas 25 000 en 298 lugares |

Decisiones de alcance:

- **Solo formas por defecto**. Las 134 formas no predeterminadas de estas especies son
  megaevoluciones, Gigamax, formas de combate (Castform, Deoxys), variantes de Pikachu o formas
  regionales de generaciones posteriores (Vulpix de Alola, Meowth de Galar…). Ninguna existe en
  los juegos de la 1.ª a la 3.ª generación. En la 4.ª, las formas de Burmy, Wormadam, Shellos,
  Gastrodon, Rotom, Giratina y Shaymin no se distinguen: se carga la forma por defecto
  ([CA-11](../01-ddf/cuestiones-abiertas.md#resueltas)). Las regionales se cargarán con la generación que las
  introduce ([RN-05](../01-ddf/reglas-negocio.md#rn-05)).
- **Juegos de la 1.ª y la 2.ª generación sin juego objetivo**. Se cargan para que el *Hall of
  Fame* y el recorrido puedan registrarlos ([RN-16](../01-ddf/reglas-negocio.md#rn-16)), con
  sus tipos y su tabla de eficacias ([RF-12](../01-ddf/requisitos-funcionales.md#rf-12)). No se
  cargan sus combates clave.
- **Solo los juegos completos son juego objetivo**
  ([RF-05](../01-ddf/requisitos-funcionales.md#rf-05),
  [CA-67](../01-ddf/cuestiones-abiertas.md#resueltas)). La fuente de PokeAPI propone como
  objetivo los 10 de la 3.ª y la 4.ª generación y, con todo cargado, `ingest/targets.py` deja
  como tales solo los completos; el informe dice qué les falta a los demás, que se cargan
  igualmente. Hoy son los 5 de la 3.ª, Diamante, Perla y Platino: tienen sus mecánicas, sus
  combates clave y su regla de llegada ([CA-28](../01-ddf/cuestiones-abiertas.md#resueltas)).
  A HeartGold y SoulSilver les faltan esos tres datos
  ([plan de la 4.ª generación](plan-cuarta-generacion.md)).
- **Solo los movimientos por nivel que exigen las evoluciones**. De `pokemon_moves.csv`
  (10,7 MB, unas 640 000 filas) se leen solo las filas aprendidas por nivel
  (`pokemon_move_method_id` 1) de un movimiento que alguna evolución exige conocer
  (`known_move_id` de `pokemon_evolution.csv`), y se guardan las de las formas y grupos de
  versiones cargados en `level_move`. El filtro va antes de validar cada fila, para que la
  lectura siga siendo rápida. Con ellas el motor decide si un paso por movimiento es tedioso
  ([CA-32](../01-ddf/cuestiones-abiertas.md#resueltas)).
- **Pokémon Showdown sigue aplazado** ([ADR-0004](../03-adr/0004-pokeapi-volcado-csv.md)).

## Cómo se interpreta el volcado de PokeAPI

El volcado CSV de `PokeAPI/pokeapi` se carga del commit fijado en `data/curated/pokeapi.yaml`
([ADR-0004](../03-adr/0004-pokeapi-volcado-csv.md)); estas reglas se comprobaron con el commit
`bc92d3b` (2026-09-30).

### Ficheros que se usan

| Fichero CSV | Destino | Filtro o transformación |
|-------------|---------|-------------------------|
| `generations.csv` | `generation` | Generaciones 1 a 4. |
| `version_groups.csv`, `versions.csv`, `version_names.csv` | `version_group`, `game` | Grupos 1 a 10. Se excluyen Colosseum y XD (no son de la saga principal) y las versiones solo japonesas (`red-green-japan`, `blue-japan`), que nunca salieron en español. Nombres en español (`local_language_id` 7). `release_order` es el id de la versión en PokeAPI. Son juego objetivo los de la 3.ª y la 4.ª generación y tienen crianza desde la 2.ª (`ingest/scope.py`). |
| `pokemon_species.csv`, `pokemon_species_names.csv` | `species` | `generation_id` ≤ 4. Si la preevolución es de una generación que no se carga, `evolves_from` queda vacío. Una preevolución de una generación posterior a la del juego no existe en él (Happiny para Chansey en Rojo Fuego): ver [crianza](#crianza). |
| `pokemon.csv`, `pokemon_forms.csv` | `pokemon` | Especie ≤ 493 e `is_default` = 1. El nombre en español es el de la especie. La forma por defecto de Deoxys es `deoxys-normal`, y la de Shaymin, `shaymin-land`. |
| `pokemon_types.csv`, `pokemon_types_past.csv` | `pokemon_type` | Resueltos por generación (ver abajo). |
| `types.csv`, `type_names.csv` | `type` | `generation_id` ≤ 4. Se excluyen los tipos especiales `unknown` y `shadow`. |
| `type_efficacy.csv`, `type_efficacy_past.csv` | `type_efficacy` | Resueltas por generación (ver abajo). |
| `pokemon_egg_groups.csv`, `egg_groups.csv` | `species_egg_group` | Sin filtro adicional. |
| `pokemon_evolution.csv`, `evolution_triggers.csv` | `evolution_step` | Ver [evoluciones](#evoluciones). Una columna de condición desconocida se carga como condición, con su texto, y la carga queda bloqueada hasta catalogarla para RN-15 y RN-20 ([CA-42](../01-ddf/cuestiones-abiertas.md#resueltas)). |
| `items.csv`, `locations.csv`, `moves.csv`, `regions.csv` | Identificadores en `conditions` | Los ids de objetos, lugares, movimientos y regiones de las condiciones se sustituyen por su identificador (`thunder-stone`, `kings-rock`…). |
| `pokedexes.csv`, `pokemon_dex_numbers.csv`, `pokedex_version_groups.csv` | `pokedex`, `pokedex_number`; propuestas de llegada | Ver [Pokédex y apariciones](#pokedex-y-apariciones). La Pokédex regional de la regla de cada juego en `arrival.yaml`: Kanto (151) para Rojo Fuego y Verde Hoja ([datos curados](datos-curados.md#arrivalyaml)). |
| `encounters.csv`, `encounter_slots.csv`, `encounter_methods.csv`, `encounter_condition_values.csv`, `encounter_condition_value_map.csv`, `location_areas.csv`, `location_names.csv` | `encounter`, `location` | Ver [Pokédex y apariciones](#pokedex-y-apariciones). |

Todos los nombres en español de las 493 especies y de los 16 juegos están en el volcado. De los
lugares, solo los de Hoenn: los de Kanto, Johto, Archi7 y Sinnoh están en los datos curados.

Cada fila se valida con un modelo pydantic (`ingest/sources/pokeapi/rows.py`): si falta una
columna o un valor no tiene el tipo esperado, la carga falla en lugar de cargar datos
erróneos.

### Cómo se interpretan los datos «antiguos»

- **`pokemon_types_past`**: cada fila indica los tipos que tenía un Pokémon **hasta** la
  generación `generation_id`, incluida. Para la generación `g` se usa la fila con el menor
  `generation_id` ≥ `g`; si no hay ninguna, los tipos actuales. Ejemplos: Clefairy es Normal
  hasta la 5.ª generación y Magnemite es solo Eléctrico en la 1.ª.
- **`type_efficacy_past`**: misma interpretación. En la 3.ª generación, Fantasma y Siniestro
  hacen ×0,5 a Acero (hasta la 5.ª). En la 1.ª, Veneno y Bicho se hacen ×2 mutuamente,
  Fantasma no afecta a Psíquico y Hielo hace ×1 a Fuego.

### Evoluciones

La columna `is_default` de `pokemon_evolution` marca el método «canónico» actual, no el de cada
juego (p. ej., la fila de Wurmple con su condición aleatoria en Rubí y Zafiro tiene
`is_default` = 0), así que no se usa.

`pokemon_evolution.version_group_id` es el grupo de versiones en el que **se introdujo** esa
evolución, no un intervalo de validez. Por ejemplo, Pichu → Pikachu figura con Oro y Plata
porque Pichu aparece en la 2.ª generación, y Chansey figura con Diamante y Perla por Happiny.
Esto corrige la interpretación anterior del DDT, que decía que un método valía «desde su grupo
de versiones hasta que otro lo sustituye».

Regla para la primera carga: un paso se aplica en un grupo de versiones si su
`version_group_id` tiene un `order` menor o igual y las dos especies están cargadas. En las
generaciones 1 a 4 no hay dos métodos para el mismo paso. Los casos con varios métodos
(Milotic: belleza en Rubí y Zafiro, intercambio con Escama Bella en Negro y Blanco y belleza
de nuevo en Rubí Omega y Zafiro Alfa) se resolverán al cargar la 5.ª generación.

Casos de las especies 1 a 493 hasta HeartGold y SoulSilver, con la clasificación de
[RN-15](../01-ddf/reglas-negocio.md#rn-15) que les corresponde:

| Disparador y condiciones | Ejemplos | ¿Tediosa? |
|--------------------------|----------|-----------|
| Subir de nivel | Bulbasaur → Ivysaur | No |
| Subir de nivel con amistad | Pichu → Pikachu, Golbat → Crobat, Chansey → Blissey | No |
| Subir de nivel con amistad y hora del día | Eevee → Espeon o Umbreon | Sí (hora del día) |
| Subir de nivel comparando estadísticas | Tyrogue → Hitmonlee, Hitmonchan o Hitmontop | Sí |
| Subir de nivel con belleza | Feebas → Milotic | Sí |
| Usar un objeto | Pikachu → Raichu, Eevee → Vaporeon | No |
| Intercambio, con o sin objeto | Haunter → Gengar, Onix → Steelix, Clamperl → Huntail | Sí |
| Subir de nivel según la personalidad (al azar) | Wurmple → Silcoon o Cascoon | Sí, por ser aleatoria ([CA-35](../01-ddf/cuestiones-abiertas.md#resueltas)); además penaliza en [RN-20](../01-ddf/reglas-negocio.md#rn-20) |
| Muda (`shed`) | Nincada → Shedinja | Sí ([CA-35](../01-ddf/cuestiones-abiertas.md#resueltas)) |
| Subir de nivel conociendo un movimiento (4.ª) | Tangela → Tangrowth, Piloswine → Mamoswine | Solo si no lo aprende por nivel desde el nivel 2 ([CA-32](../01-ddf/cuestiones-abiertas.md#resueltas)): Mamoswine sí, Tangrowth no |
| Subir de nivel en un lugar (4.ª) | Magneton → Magnezone, Eevee → Leafeon | Sí (lugar) |
| Subir de nivel con un Pokémon en el equipo (4.ª) | Mantyke → Mantine | Sí (equipo) |
| Subir de nivel llevando un objeto, según la hora (4.ª) | Sneasel → Weavile, Happiny → Chansey | Sí (hora del día) |
| Usar un objeto, según el sexo (4.ª) | Kirlia → Gallade, Snorunt → Froslass | No ([CA-43](../01-ddf/cuestiones-abiertas.md#resueltas)) |

La ingesta guarda el disparador y las condiciones tal como vienen. Decidir si un paso es
tedioso o aleatorio lo hace `core/evolution.py` ([modelo de datos](modelo-datos.md#evoluciones)).
En PokeAPI, las evoluciones aleatorias se reconocen por `percentage_chance` o
`condition_expression`.

### Crianza

- Una línea se puede criar si alguna de sus especies tiene un grupo huevo distinto de
  `no-eggs` y de `ditto` ([RN-11](../01-ddf/reglas-negocio.md#rn-11)). Ejemplo: Nidorina y
  Nidoqueen están en `no-eggs`, pero Nidoran♀ cría y la línea es válida.
- En las generaciones 1 a 3 hay 34 especies en `no-eggs`: los 21 legendarios y singulares,
  los 10 bebés, Unown, Nidorina y Nidoqueen. Ditto es el único del grupo `ditto`.
- La etapa que nace del huevo es la primera de la cadena que existe en la generación del juego:
  en Rojo Fuego, Chansey, porque Happiny es de la 4.ª. Lo aplican la propuesta de llegada de la
  ingesta y la API al construir las etapas.
- Los bebés de incienso (Azurill y Wynaut en la 3.ª generación; Budew, Chingling, Bonsly,
  Mime Jr., Happiny, Munchlax y Mantyke en la 4.ª) solo nacen si un progenitor lleva un
  incienso; sin él nace la etapa siguiente. Se toma como etapa de entrada la que nace sin
  incienso (Marill, Wobbuffet, Roselia…). La ingesta marca esos bebés con
  `species.requires_incense` y `core/breeding.py` aplica la decisión
  ([CA-36](../01-ddf/cuestiones-abiertas.md#resueltas)).

### Existencia y llegada

- **Existencia** ([RN-03](../01-ddf/reglas-negocio.md#rn-03)): en cada juego de la 3.ª y la 4.ª
  generación se pueden tener todas las especies hasta su generación (386 en la 3.ª, 493 en la
  4.ª), al menos por intercambio. Se carga como dato automático.
- **Llegada antes de completar el juego**
  ([CA-28](../01-ddf/cuestiones-abiertas.md#resueltas)):
    dato **inferido** en los juegos con regla de llegada, la de cada uno en
    [`arrival.yaml`](datos-curados.md#arrivalyaml): la Pokédex de Kanto en Rojo Fuego y Verde
    Hoja, la de Hoenn en Esmeralda y la Nacional en Rubí y Zafiro
    ([restricciones comprobadas](datos-requeridos.md#restricciones-de-llegada-por-juego)). El
    usuario lo confirma antes de generar ([RN-18](../01-ddf/reglas-negocio.md#rn-18)). En un
    juego sin regla queda **pendiente**, y entonces le faltan «los Pokémon que existen y pueden
    llegar» y no puede ser juego objetivo ([catálogo de juegos](#catalogo-de-juegos)).

### Pokédex y apariciones

Para la Pokédex de los juegos superados
([ADR-0013](../03-adr/0013-obtencion-pokeapi-y-curados.md)):

- **Pokédex**: se cargan la Nacional y las de los grupos de versiones cargados
  (`pokedex_version_groups.csv`): Kanto, Johto original, Hoenn, Sinnoh original, Sinnoh
  ampliada y Johto actualizada. De cada una, solo los números de las especies cargadas: la
  Nacional tiene 493. Qué Pokédex completa cada juego es un dato
  curado ([`pokedex.yaml`](datos-curados.md#pokedexyaml)).
- **Apariciones**: las de las versiones de los 16 juegos cargados, cada una con su lugar
  (`location_areas.csv` da el lugar y la zona), su método (`encounter_methods.csv`) y sus
  condiciones (`encounter_condition_value_map.csv`), tal como vienen. Todas las formas de las
  apariciones son formas por defecto de especies cargadas; si no, la carga falla.
- **Una fila por Pokémon, zona, método y condiciones**: PokeAPI da una fila por hueco
  (`encounter_slots.csv`) y cada hueco tiene su probabilidad (`rarity`) dentro de su zona y su
  método. Las filas del mismo Pokémon se unen: sus probabilidades se suman y sus niveles forman
  un intervalo. Ekans en la Ruta 4 de Rojo Fuego ocupa cuatro huecos (10, 10, 4 y 1 %): una fila
  del 25 %, de nivel 6 a 12. La suma se limita al 100 %: los varios Voltorb estáticos de la
  Central de Energía de Amarillo suman 200.
- **Cada condición, su fila**: en la 2.ª generación, una misma zona tiene una fila por momento
  del día (`time-morning`, `time-day`, `time-night`), con su probabilidad
  ([CA-81](../01-ddf/cuestiones-abiertas.md#resueltas)).
- **Lo que PokeAPI ya distingue con las condiciones**: los fósiles son regalos con la condición
  del fósil (`item-helix-fossil`) y el perro legendario errante de Rojo Fuego y Verde Hoja lleva
  el inicial del que depende (`starter-squirtle`,
  [CA-80](../01-ddf/cuestiones-abiertas.md#resueltas)). No hacen falta datos curados para ellos.
- **También los métodos de spin-offs** (los discos extra de Colosseum y Pokémon Channel, y el
  huevo de Manaphy de Pokémon Ranger): es
  `core/` quien los omite y quien deduce que un Pokémon que solo se obtiene así es imposible de
  forma automática ([RN-25](../01-ddf/reglas-negocio.md#rn-25)).
- **Lugares**: los que tienen apariciones. El nombre en español sale de `location_names.csv` o,
  si no está, de [`locations.yaml`](datos-curados.md#locationsyaml); si no está en ninguno, el
  lugar se carga con `name_es` nulo y el informe lo avisa. De los curados sale también el objeto
  de evento sin el que no se llega a algunos lugares (Roca Ombligo, Isla Origen, Isla Suprema,
  Isla del Sur, Isla Lunanueva, Paraíso Floral y Sala del Origen).

Clasificar cada método en las formas de [RN-26](../01-ddf/reglas-negocio.md#rn-26) (regalo,
salvaje, errante…) es una regla de negocio y se hace en `core/`. La carga solo comprueba que no
aparece ningún método sin clasificar ([comprobaciones](#comprobaciones-de-la-carga)).

## Catálogo de juegos

[`catalog.yaml`](datos-curados.md#catalogyaml) dice qué juegos tiene el catálogo
([RF-25](../01-ddf/requisitos-funcionales.md#rf-25)); la fuente de PokeAPI añade a cada uno su
nombre en español (`version_names.csv`) y su generación (la de su grupo de versiones), también a
los que no se cargan. Al final de la carga, `ingest/targets.py` guarda en `catalog_game.missing`
lo que le falta a cada juego para estar completo: lo mismo que deja un juego cargado sin ser
juego objetivo o, si el juego no se carga, `generation_not_loaded`.

Hoy no les falta nada a los 5 de la 3.ª generación ni a Diamante, Perla y Platino. A HeartGold
y SoulSilver les faltan sus Pokémon disponibles (no tienen regla de llegada), sus mecánicas y
sus combates clave. A Oro, Plata y
Cristal, lo mismo, porque la 2.ª generación no es de juegos objetivo (`ingest/scope.py`); y a los
de la 5.ª en adelante, su generación.

## WikiDex

- Una petición por página de entrenador (`action=parse&prop=wikitext`): 13 para Rojo Fuego y
  Verde Hoja, 17 para Rubí, Zafiro y Esmeralda y 15 para Diamante, Perla y Platino (las mismas
  páginas en los tres).
- Caché permanente en `data/cache/wikidex/`, como mucho una petición por segundo y un
  `User-Agent` descriptivo. Una segunda ejecución no hace peticiones
  ([ingesta](../05-operacion/ingesta.md#wikidex)).
- Las plantillas `{{Equipo}}` se procesan con mwparserfromhell. La lista curada dice en qué
  sección y bajo qué rótulo está cada equipo; las revanchas no se cargan. Del rival se quita
  el inicial y, si hay variantes según el inicial, solo se guardan los Pokémon comunes a
  todas ([datos curados](datos-curados.md#key_battlesyaml)). Lo que no se encuentre hace fallar la
  carga con un mensaje que dice qué falta.
- Licencia CC BY-NC-SA: cada combate guarda la página y la revisión de WikiDex de su equipo,
  para la atribución ([ADR-0004](../03-adr/0004-pokeapi-volcado-csv.md)).

## Comprobaciones de la carga

Antes de sustituir la base de datos, la ingesta ejecuta estas comprobaciones
(`ingest/checks.py`). Si alguna falla, la carga se rechaza y se conserva la anterior
([ingesta](../05-operacion/ingesta.md#que-hace)).


- **Cantidades**: 4 generaciones, 10 grupos de versiones, 16 juegos, 17 tipos, 493 especies,
  493 formas, 5 × 386 + 5 × 493 filas de disponibilidad, 7 Pokédex, 16 Pokédex de juego, 95
  transferencias y 60 Pokémon de evento. Tablas de eficacias completas: 15 × 15 pares
  en la 1.ª generación y 17 × 17 de la 2.ª a la 4.ª.
- **Juegos objetivo**: exactamente los completos: los 5 de la 3.ª generación, Diamante, Perla y
  Platino.
- **Catálogo de juegos**: 36 juegos; todos los cargados están en él; casos conocidos de nombre,
  generación, plataforma, si reciben un Pokémon criado, si son jugables y qué les falta (nada a
  Rojo Fuego, Esmeralda ni Diamante; a HeartGold, sus Pokémon disponibles, sus mecánicas y sus
  combates clave; la generación a Negro y a Leyendas: Z-A); Let's Go no está.
- **Tipos por generación**: Clefairy es Normal en la 3.ª, Magnemite es solo Eléctrico en la
  1.ª y Eléctrico/Acero en la 2.ª, y Bulbasaur es Planta/Veneno.
- **Eficacias**: Fantasma no afecta a Psíquico en la 1.ª y le hace ×2 en la 3.ª, Fantasma
  hace ×0,5 a Acero en la 3.ª y Veneno hace ×2 a Bicho en la 1.ª.
- **Evoluciones**: Pichu → Pikachu no existe en Rojo y Azul y es por amistad en Oro y Plata;
  Haunter → Gengar es por intercambio; Wurmple → Silcoon es aleatoria; Nincada → Shedinja es
  por muda; Feebas → Milotic es por belleza en Rubí y Zafiro.
- **Crianza**: Mewtwo es legendario y Ditto está en el grupo huevo `ditto`.


- **Datos curados**: 16 mecánicas (2 por juego con datos curados) y sus combates clave, con su
  número, el primero y el último: 13 en Rojo Fuego y Verde Hoja, de Brock a Azul (eran 15 hasta
  que CA-39 quitó los dos de Giovanni como jefe del Team Rocket); 15 en Rubí y Zafiro, de Petra a
  Máximo; 16 en Esmeralda, de Petra a Plubio, y 15 en Diamante, Perla y Platino, de Roco a
  Cintia. Numerados del 1 en adelante en cada juego, cada uno con Pokémon, y equipos conocidos:
  Brock, el Campeón de Rojo Fuego, Petra, Magno, Aquiles, Blasco, Helio en Diamante, y Fantina e
  Israel en Platino. Cada versión de Rubí y Zafiro solo tiene su jefe
  ([CA-88](../01-ddf/cuestiones-abiertas.md#resueltas)).
- **Iniciales**: 3 por juego de la 2.ª a la 4.ª generación y de Rojo y Azul, y Raichu en
  Amarillo: Venusaur, Charizard y Blastoise en Rojo Fuego; Sceptile, Blaziken y Swampert en
  Esmeralda; Torterra, Infernape y Empoleon en Platino, y Meganium, Typhlosion y Feraligatr en
  Cristal y HeartGold. Ninguno evoluciona en su juego: todos son la
  evolución final ([CA-59](../01-ddf/cuestiones-abiertas.md#resueltas)).
- **Bebés de incienso**: exactamente Azurill y Wynaut, y los 7 de la 4.ª generación.
- **Pokédex** ([RN-22](../01-ddf/reglas-negocio.md#rn-22)): 7 Pokédex, con 493 especies en la
  Nacional, 151 en Kanto, 251 en Johto, 202 en Hoenn, 151 en Sinnoh original, 210 en Sinnoh
  ampliada y 256 en Johto actualizada. Rojo completa la de Kanto, Cristal la de Johto, y Rojo
  Fuego, Platino y Plata SoulSilver, la Nacional.
- **Apariciones** ([RN-26](../01-ddf/reglas-negocio.md#rn-26)): ningún método fuera de los que
  clasifica `core/`. Casos conocidos en Rojo Fuego: Eevee, Lapras y Hitmonlee son regalos;
  Lapras también aparece surfeando; Omanyte y Aerodactyl son regalos con su fósil; Snorlax, con
  la Poké Flauta; Zapdos, estático; Raikou, errante si se eligió a Squirtle; Ekans, salvaje; ni
  Sandshrew ni Mew aparecen. En Oro, Suicune es errante y Togepi, un huevo de regalo. Mew es de
  evento en Rojo Fuego y a la Roca Ombligo solo se llega con el Misti-ticket. En Diamante,
  Munchlax sale en los árboles de miel, Darkrai es estático (en la Isla Lunanueva, a la que solo
  se llega con el Carné de Socio) y Turtwig es un regalo.
- **Transferencias** ([RN-25](../01-ddf/reglas-negocio.md#rn-25)): de Rojo a Oro, solo especies de la 1.ª
  generación; de Oro a Plata, de Rojo Fuego a Rubí, de Diamante a Plata SoulSilver y de
  Esmeralda a Platino (Parque Compi), sin límite; de Cristal a Esmeralda y de Platino a
  Esmeralda, no se puede.
- **Propuestas de llegada**: inferidas en los juegos con regla de llegada (los de la 3.ª
  generación, Diamante, Perla y Platino) y pendientes en HeartGold y SoulSilver. En Diamante y
  Platino llegan Bulbasaur, Garchomp y Crobat. Casos conocidos en Rojo Fuego: llegan Bulbasaur,
  Vaporeon, Golbat y Chansey (que nace como Chansey, porque Happiny es de la 4.ª), y no llegan
  Pikachu, Raichu, Clefairy, Crobat, Espeon ni Blissey.

- **Equipos de los combates clave**: cada combate de Rojo Fuego y Verde Hoja tiene Pokémon
  (las claves foráneas garantizan que son formas cargadas) y es automático. Giovanni solo
  aparece como líder de gimnasio (CA-39). El equipo de Brock en Rojo Fuego es Geodude y Onix,
  y el del Campeón, Pidgeot, Alakazam y Rhydon (CA-26 y CA-38).

Los casos que la aplicación no sabe tratar (métodos de evolución sin catalogar, movimientos
por nivel, equipos que no están en WikiDex) son **bloqueos** de la carga, no errores
([ADR-0008](../03-adr/0008-cargas-bloqueadas.md),
[bloqueos](../05-operacion/ingesta.md#bloqueos)).
