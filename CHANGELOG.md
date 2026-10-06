# Historial de versiones

Cambios relevantes de cada versión. El proyecto sigue [SemVer](https://semver.org/lang/es/) y
el formato de [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Cómo se publica una
versión: [versiones](docs/05-operacion/versiones.md).

## [Sin publicar]

### Añadido

- **Ingesta**: descarga la imagen de cada Pokémon (sus *sprites* de PokeAPI, del commit fijado
  en `data/curated/pokeapi.yaml`) a la caché local, sin versionarlas en git. Una imagen que
  falta no rompe la carga: el informe la avisa (RF-17, ADR-0010, #49).
- **Web**: cada Pokémon se muestra con su imagen junto al nombre en el catálogo, la ficha y su
  línea evolutiva, los favoritos, el resultado, el selector del equipo y el *Hall of Fame*. Sin
  imagen se muestra igual. Al pie, el aviso de la titularidad de las imágenes y la procedencia
  de los datos (RF-17, CA-56).
- **API**: `GET /api/pokemon/{pokemon}/image` sirve la imagen de cada forma desde la caché
  local, y las respuestas con Pokémon (catálogo, ficha, favoritos, generación y *Hall of Fame*)
  incluyen `image_url`. `/api/meta` da el commit de las imágenes (`sprites_commit`) (RF-17).
- **API**: si `reference.sqlite` es de una versión anterior y le faltan datos, responde `503`
  pidiendo repetir la carga, en lugar de fallar.

### Cambiado

- **Hay que repetir la carga de datos** (`uv run python -m ingest`) al actualizar: la tabla
  `pokemon` guarda ahora el identificador de PokeAPI y la imagen de cada forma. En el
  servidor, copia también las imágenes ([puesta en producción](docs/05-operacion/puesta-en-produccion.md#4-codigo-web-y-datos)).
- El aviso de la web cuando no hay datos se titula «Hay que cargar los datos».
- **Comprobar el equipo elegido** (`POST /api/games/{game}/team-checks`) ya no genera los equipos
  otra vez: solo resuelve las reglas de presencia. Pasa de unos 40 ms a menos de 1 ms en Rojo
  Fuego (#59).

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

[Sin publicar]: https://github.com/AlbertoMercado/pokemon-team-builder/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/AlbertoMercado/pokemon-team-builder/releases/tag/v1.0.0
