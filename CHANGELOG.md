# Historial de versiones

Cambios relevantes de cada versión. El proyecto sigue [SemVer](https://semver.org/lang/es/) y
el formato de [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Cómo se publica una
versión: [versiones](docs/05-operacion/versiones.md).

## [Sin publicar]

### Corregido

- **Web**: en la lista inicial de la Pokédex y en el equipo de cada registro del *Hall of Fame*,
  todas las tarjetas de Pokémon tienen la misma altura. Antes, los tipos bajaban a otra línea
  solo cuando no cabían junto al nombre, y unas tarjetas eran más altas que otras.

## [1.5.0] - 2026-10-10

Nueva sección **Pokédex**: cada juego que has superado tiene su Pokédex, y la aplicación te
propone uno a uno el siguiente Pokémon que registrar y la forma más sencilla de obtenerlo
(RF-20 a RF-24, #94). Por eso, cada juego se registra una sola vez en el *Hall of Fame*.

**Al actualizar hay que repetir la carga de datos** (`uv run python -m ingest`, o
`scripts/start.sh`, que la hace): trae las Pokédex, las apariciones y los iniciales de todos
los juegos. Hasta repetirla, la API pide hacerlo. Al arrancar, la API migra `user.sqlite` a las
tablas de la Pokédex; si algún juego estuviera registrado más de una vez en el *Hall of Fame*,
no arranca y dice cuál: elimina con la versión anterior los registros que sobren.

### Añadido

- **Pokédex** en la web: el progreso de cada juego superado; la primera vez, la lista para
  marcar los que ya tienes; después, el siguiente Pokémon que registrar con la forma más
  sencilla de obtenerlo (evolucionarlo, criarlo, transferirlo de otro juego, dónde aparece y
  con qué probabilidad, regalos y eventos), con las demás formas para elegir otra y la opción de
  saltarlo de momento; y el detalle de registrados e imposibles para corregir errores (RF-20 a
  RF-24, RN-22 a RN-26, #101, #103).
- **API de la Pokédex** (`/api/pokedex`): el progreso, la lista inicial, el Pokémon objetivo, la
  ficha con todas las formas de obtención y las marcas de cada Pokémon (#102).
- **Ingesta**: carga la Pokédex de cada juego, dónde y cómo se obtiene cada Pokémon en los 11
  juegos (lugar, método, probabilidad y niveles), qué juegos pueden enviarse Pokémon, los
  Pokémon de evento, los nombres en español de todos los lugares y los iniciales de todos los
  juegos, no solo de los objetivo (#100, #102).
- **Arranque**: `scripts/start.sh` prepara y arranca la aplicación en un solo comando: copia
  `user.sqlite` en `data/backups/`, instala las dependencias, carga los datos, compila la web y
  arranca la API, que la sirve. Acepta las opciones de la carga, como `--offline` (#93).

### Cambiado

- **Hall of Fame**: cada juego se registra una sola vez. Un juego registrado deja de aparecer en
  **Nuevo juego** y en el formulario del *Hall of Fame*, y la API responde `409` si se intenta
  revisar, generar o registrar otra vez. Tras registrar un equipo desde el resultado, ya no se
  vuelve a generar. Para volver a jugar un juego, se elimina antes su registro (CA-68, #97).
- **Hall of Fame**: borrar un registro, o cambiarle el juego, borra su Pokédex; si ya la habías
  empezado, la web lo avisa antes (CA-68, #102, #103).

### Pendiente

- Mecánicas y combates clave de Rubí, Zafiro y Esmeralda, para poder elegirlos como juego
  objetivo, y restricciones de llegada del resto de juegos (CA-28, #8).
- Bloqueos de la carga: informe y código de salida 2 (RF-16, #78).
- Pruebas más robustas de la web (#77).
- Sin prioridad: puesta en producción (ADR-0009, #51) y protección del acceso (RF-19, #52).

## [1.4.0] - 2026-10-07

Solo se pueden elegir como juego objetivo los juegos completos, los que tienen todos los datos
que necesitan las reglas. Hoy son Rojo Fuego y Verde Hoja.

**Al actualizar hay que repetir la carga de datos** (`uv run python -m ingest`): es la carga la
que decide qué juegos están completos y, hasta repetirla, **Nuevo juego** sigue ofreciendo
Rubí, Zafiro y Esmeralda.

### Añadido

- **Ingesta**: el informe de la carga lista los juegos que no se pueden elegir como objetivo y
  qué les falta: sus mecánicas, sus combates clave, sus iniciales o la disponibilidad de sus
  Pokémon. Un juego incompleto no bloquea la carga (CA-67, #75, #91).

### Cambiado

- **Juegos objetivo**: solo se pueden elegir los juegos completos (RF-05, CA-67). Rubí, Zafiro
  y Esmeralda, a los que les faltan sus mecánicas y sus combates clave, dejan de aparecer en
  **Nuevo juego** y responden `404` en la revisión y la generación, aunque se siguen cargando y
  se pueden registrar en el *Hall of Fame*. Un juego sin combates clave deja de ser un motivo
  para bloquear la carga, como decía CA-46 (#75, #90, #91).

## [1.3.0] - 2026-10-07

Nueva regla de presencia RN-21: el equipo lleva un inicial del juego, y solo uno. Si ninguno de
tus favoritos es inicial, la regla elige uno de los del juego.

**Al actualizar hay que repetir la carga de datos** (`uv run python -m ingest`): la base de
referencia tiene una tabla nueva con los iniciales de cada juego y, hasta repetirla, la API
responde `503` pidiéndolo.

### Añadido

- **Reglas**: regla de presencia RN-21, activa por defecto: el equipo incluye un inicial del
  juego en su evolución final (en Rojo Fuego y Verde Hoja, Venusaur, Charizard o Blastoise), y
  ningún otro miembro de las líneas de los iniciales. Si ningún inicial es favorito, la regla
  elige uno del juego, que el resultado marca como «No es favorito», y antes de generar se
  piden también los datos sin verificar de los iniciales (CA-59 a CA-66, #85, #86, #88).
- **Datos**: la carga guarda los iniciales de los cinco juegos objetivo, a partir del nuevo
  fichero curado `data/curated/starters.yaml`, y comprueba que cada uno es una evolución final
  en su juego (#85, #87).
- **API**: nuevo estado de presencia `chosen`, cuando una regla pone en el equipo un Pokémon
  que no es favorito (RN-21, #88).
- **Documentación**: [referencia de la API](docs/02-ddt/api-referencia.md) generada del contrato
  OpenAPI al construir la documentación, con todos los endpoints, parámetros y campos descritos;
  un test exige que no falte ninguna descripción (ADR-0012, #76).

### Cambiado

- **Motor**: las reglas de presencia se cumplen por orden (RN-13, RN-14 y RN-21) y, si chocan,
  solo cede la que no cabe con las anteriores (CA-61, #88).
- **Resultados**: con RN-21 activa, los equipos recomendados cambian. Con los favoritos del
  escenario de Rojo Fuego, cada equipo lleva a Venusaur o a Blastoise (#88).
- **Web**: en la revisión de datos, el grupo «Favoritos» pasa a ser «Favoritos e iniciales del
  juego» (#88).

## [1.2.0] - 2026-10-07

Portadas de los juegos (RF-18): cada juego se ve con su portada junto al nombre, y cada combate
clave enlaza a la página de WikiDex de la que sale su equipo. Corrige además la altura de las
filas de Pokémon en el móvil.

**Al actualizar hay que repetir la carga de datos** (`uv run python -m ingest`): la tabla `game`
tiene columnas nuevas y, hasta repetirla, la API responde `503` pidiéndolo. En el servidor, copia
también las portadas
([puesta en producción](docs/05-operacion/puesta-en-produccion.md#4-codigo-web-y-datos)).

**Las portadas son solo para uso privado**: WikiDex las declara de uso legítimo solo en sus
artículos (ADR-0011). Si alguna vez publicas la aplicación de forma abierta, carga los datos con
`--no-covers`.

### Añadido

- **Ingesta**: descarga la portada de cada juego cargado de WikiDex a la caché local, con
  límite de peticiones, comprobación de su `sha1` y sin versionarlas en git. Cada portada se
  indica en `data/curated/covers.yaml`. `--no-covers` carga sin ellas (RF-18, ADR-0011, #69,
  #70).
- **API**: `GET /api/games/{game}/cover` sirve la portada de cada juego cargado. Los juegos y el
  *Hall of Fame* la indican en `cover_url`, con la página de WikiDex de la que sale en
  `cover_source_url`. En la revisión de datos, cada combate clave enlaza en `source_url` a la
  versión de la página de WikiDex de la que sale su equipo (RF-18, ADR-0004, ADR-0011, #71).
- **Web**: cada juego se muestra con su portada junto al nombre: al elegir el juego, en la
  revisión de datos y el resultado, en el último juego completado del Inicio y en el *Hall of
  Fame*. Sin portada se muestra igual. El pie añade su titularidad y un enlace a la página de
  cada portada en WikiDex. En la revisión, cada combate clave con fuente conocida muestra
  «Fuente: WikiDex» (RF-18, CA-56, ADR-0004, ADR-0011, #72).

### Corregido

- **Web**: en el móvil, todas las filas del catálogo, los favoritos, las sugerencias del
  resultado y la línea evolutiva miden lo mismo, con el número y el nombre arriba, los tipos
  debajo y la estrella siempre a la derecha. Antes, con un nombre largo o dos tipos, la estrella
  bajaba sola a otra línea y la fila salía más alta (RF-01, RF-04, #68, #73).

### Pendiente

- Mostrar la fuente de cada combate clave fuera de la revisión: con los datos actuales los
  combates se cargan automáticos y la revisión no los muestra (ADR-0004).
- Aprobar la puesta en producción (ADR-0009, #51), proteger el acceso (RF-19, #52) y las
  restricciones de llegada del resto de juegos (CA-28, #8).

## [1.1.1] - 2026-10-06

Corrección de las imágenes de la 1.1.0. Basta con actualizar y compilar la web: no hace falta
repetir la carga de datos.

### Corregido

- **Web**: las imágenes de los Pokémon respetan su tamaño, así que todas las filas de las listas
  miden lo mismo. El estilo base de Tailwind (`height: auto`) hacía que los Pokémon altos y
  estrechos, como Kakuna, salieran casi el doble de altos (RF-17, #65, #66).

## [1.1.0] - 2026-10-06

Imágenes de los Pokémon (RF-17): cada Pokémon se ve con su imagen en toda la aplicación, sin
depender de servidores externos una vez cargados los datos.

**Al actualizar hay que repetir la carga de datos** (`uv run python -m ingest`): la tabla
`pokemon` tiene columnas nuevas y, hasta repetirla, la API responde `503` pidiéndolo. En el
servidor, copia también las imágenes
([puesta en producción](docs/05-operacion/puesta-en-produccion.md#4-codigo-web-y-datos)).

### Añadido

- **Ingesta**: descarga las imágenes de cada Pokémon del repositorio PokeAPI/sprites, fijado a
  un commit en `data/curated/pokeapi.yaml`, a la caché local y sin versionarlas en git: su
  *sprite*, que recorta a la figura, y su ilustración oficial, que reduce a 256 px. Una imagen
  que falta no rompe la carga: el informe la avisa. Nueva dependencia: Pillow (RF-17,
  ADR-0010, #58, #63).
- **API**: `GET /api/pokemon/{pokemon}/image` y `/artwork` sirven la imagen y la ilustración de
  cada forma desde la caché local. Las respuestas con Pokémon (catálogo, ficha, favoritos,
  generación y *Hall of Fame*) incluyen `image_url`, y la ficha, `artwork_url`. `/api/meta` da
  el commit de las imágenes (`sprites_commit`) (RF-17, #61, #63).
- **API**: si `reference.sqlite` es de una versión anterior y le faltan datos, responde `503`
  pidiendo repetir la carga, en lugar de fallar (#58).
- **Web**: cada Pokémon se muestra con su imagen junto al nombre en el catálogo, la ficha y su
  línea evolutiva, los favoritos, el resultado, el selector del equipo y el *Hall of Fame*: su
  *sprite* recortado en las listas y su ilustración oficial en la ficha. Sin imagen se muestra
  igual. Al pie, el aviso de la titularidad de las imágenes y la procedencia de los datos
  (RF-17, CA-56, #62, #63).

### Cambiado

- **Comprobar el equipo elegido** (`POST /api/games/{game}/team-checks`) ya no genera los
  equipos otra vez: solo resuelve las reglas de presencia. Pasa de unos 40 ms a menos de 1 ms
  en Rojo Fuego, y la suite de tests de unos 90 s a 22 s (RN-13, RN-14, #59, #60).
- El aviso de la web cuando no hay datos se titula «Hay que cargar los datos», porque también
  sale cuando los datos son de una versión anterior (#58).

### Pendiente

- Portadas de los juegos (RF-18, #49): falta comprobar si WikiDex las tiene y se pueden usar
  (CA-55).
- Mostrar la página y la revisión de WikiDex de cada combate clave (ADR-0004).
- Aprobar la puesta en producción (ADR-0009, #51), proteger el acceso (RF-19, #52) y las
  restricciones de llegada del resto de juegos (CA-28, #8).

## [1.0.0] - 2026-10-06

Primera versión estable: la aplicación genera equipos de punta a punta, desde la carga de datos
hasta la web, y ya se usa con datos reales. Juegos objetivo completos: **Rojo Fuego y Verde
Hoja**.

### Añadido

- **Ingesta** (`uv run python -m ingest`): construye `reference.sqlite` a partir del volcado
  CSV de PokeAPI fijado a un commit (ADR-0004), los datos curados en YAML (ADR-0005) y los
  equipos de los combates clave de WikiDex, con caché local y límite de peticiones. Genera un
  informe, sustituye la base de datos solo si la carga es correcta, bloquea las cargas que
  necesitan una decisión (ADR-0008) y comprueba que no rompe las claves de `user.sqlite`.
- **Motor de reglas** (`core/`, sin I/O): filtros por candidato (llegada, crianza y recorrido),
  reglas blandas con pesos configurables, reglas de equipo, búsqueda exacta del mejor equipo
  (ADR-0006), equipo incompleto con sugerencias, agrupación de empates (RN-19) y revisión de
  los datos sin verificar (RN-18).
- **API** (FastAPI): metadatos, catálogo de Pokémon, favoritos, reglas, juegos objetivo,
  revisión de datos, generación de equipos, comprobación del equipo elegido y *Hall of Fame*.
  `user.sqlite` con migraciones de Alembic que se aplican al arrancar.
- **Web** (React + Vite + TypeScript + Tailwind): Inicio, catálogo y ficha, favoritos, reglas,
  nuevo juego con la revisión de datos, resultado de la generación, selector del equipo y
  *Hall of Fame*. La API sirve la web compilada en un solo proceso.
- **Calidad**: CI con Python (ruff, mypy estricto, import-linter, pytest e hypothesis),
  documentación (`mkdocs build --strict`), web (cliente de la API al día, ESLint, Prettier,
  Vitest y compilación), E2E con Playwright y gitleaks.
- **Documentación**: DDF (RF-XX, RN-XX, CA-XX), DDT, ADR 0001 a 0009, manual de usuario y
  operación.

### Corregido

- Los descartes del motor se explican con los nombres de los Pokémon (#47).

### Pendiente

- Aprobar la puesta en producción (ADR-0009, *Propuesto*) (#51).
- Mejoras previstas: imágenes de los Pokémon y portadas (RF-17, RF-18, #49) y protección del
  acceso (RF-19, #52).
- Restricciones de llegada del resto de juegos (CA-28, #8).

[Sin publicar]: https://github.com/AlbertoMercado/pokemon-team-builder/compare/v1.5.0...HEAD
[1.5.0]: https://github.com/AlbertoMercado/pokemon-team-builder/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/AlbertoMercado/pokemon-team-builder/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/AlbertoMercado/pokemon-team-builder/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/AlbertoMercado/pokemon-team-builder/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/AlbertoMercado/pokemon-team-builder/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/AlbertoMercado/pokemon-team-builder/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/AlbertoMercado/pokemon-team-builder/releases/tag/v1.0.0
