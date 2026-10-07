# Historial de versiones

Cambios relevantes de cada versión. El proyecto sigue [SemVer](https://semver.org/lang/es/) y
el formato de [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Cómo se publica una
versión: [versiones](docs/05-operacion/versiones.md).

## [Sin publicar]

### Añadido

- **Ingesta**: descarga la portada de cada juego cargado de WikiDex a la caché local, con
  límite de peticiones y sin versionarlas en git. Cada portada se indica en
  `data/curated/covers.yaml`. WikiDex las declara de uso legítimo solo en sus artículos, así
  que la aplicación las usa en privado; `--no-covers` carga sin ellas (RF-18, ADR-0011, #49).
- **API**: `GET /api/games/{game}/cover` sirve la portada de cada juego cargado. Los juegos y el
  Hall of Fame la indican en `cover_url`, con la página de WikiDex de la que sale en
  `cover_source_url`. En la revisión de datos, cada combate clave enlaza en `source_url` a la
  versión de la página de WikiDex de la que sale su equipo (RF-18, ADR-0004, ADR-0011, #49).
- **Web**: cada juego se muestra con su portada junto al nombre: al elegir el juego, en la
  revisión de datos y el resultado, en el último juego completado del Inicio y en el Hall of
  Fame. El pie añade su titularidad y un enlace a la página de cada portada en WikiDex. En la
  revisión, cada combate clave enlaza a la página de WikiDex de la que sale su equipo
  (RF-18, ADR-0004, ADR-0011, #49).

### Cambiado

- **Hay que repetir la carga de datos** al actualizar: la tabla `game` guarda ahora la portada
  de cada juego.

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

[Sin publicar]: https://github.com/AlbertoMercado/pokemon-team-builder/compare/v1.1.1...HEAD
[1.1.1]: https://github.com/AlbertoMercado/pokemon-team-builder/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/AlbertoMercado/pokemon-team-builder/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/AlbertoMercado/pokemon-team-builder/releases/tag/v1.0.0
