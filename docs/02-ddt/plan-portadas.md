# Plan de las portadas de los juegos

Plan para mostrar la portada de cada juego en la web
([RF-18](../01-ddf/requisitos-funcionales.md#rf-18)) y la fuente en WikiDex de cada combate
clave ([ADR-0004](../03-adr/0004-pokeapi-volcado-csv.md#acciones-derivadas)), lo que queda de la
issue #49 tras las imágenes de los Pokémon ([plan](plan-imagenes.md)). La decisión de
arquitectura está en [ADR-0011](../03-adr/0011-portadas-wikidex-uso-privado.md).

## Alcance

**Dentro**:

| Bloque | Requisitos y decisiones |
|--------|-------------------------|
| La ingesta descarga la portada de cada juego cargado de WikiDex, con caché y límite de peticiones | [CA-55](../01-ddf/cuestiones-abiertas.md#resueltas), ADR-0011 |
| La API sirve las portadas e indica en sus respuestas qué juegos tienen portada | RF-18, ADR-0011 |
| La web muestra la portada junto al nombre del juego allí donde aparece | RF-18 |
| Aviso de la titularidad y la procedencia de las portadas | [CA-56](../01-ddf/cuestiones-abiertas.md#resueltas) |
| La fuente en WikiDex de cada combate clave en la revisión de datos | ADR-0004 |

**Fuera**: otras imágenes de los juegos (logos, iconos de la consola virtual) y portadas de
juegos que no están cargados.

## Principios

Los mismos que las imágenes de los Pokémon ([principios](plan-imagenes.md#principios)): la
portada acompaña al nombre y nunca lo sustituye (`alt=""`), sin portada no hay errores, nada
externo después de la carga y las portadas no se versionan ni se redistribuyen. Además:

- **Solo uso privado** (ADR-0011): WikiDex declara sus carátulas de uso legítimo solo en sus
  artículos. La aplicación las usa en privado, con aviso y enlace a su página, y se pueden quitar
  cargando sin portadas.
- **WikiDex con cuidado**: caché permanente, al menos 1 s entre peticiones y `User-Agent`
  descriptivo, como con las páginas de los combates clave.

## Comprobaciones previas

Hechas el 2026-10-06 con la API MediaWiki de WikiDex. La portada de cada juego es la que muestra
la ficha de su artículo:

| Juego | Fichero en WikiDex | Formato | Tamaño | `sha1` |
|-------|--------------------|---------|--------|--------|
| Rojo | `Carátula de Pokémon Rojo.jpg` | JPEG | 456 × 453, 88 KB | `7ef93d10e6…` |
| Azul | `Carátula de Pokémon Azul.jpg` | JPEG | 456 × 453, 84 KB | `1555b49c13…` |
| Amarillo | `Pokémon Amarillo.png` | PNG | 456 × 453, 495 KB | `718d98b67f…` |
| Oro | `Pokemon Edición Oro.jpg` | JPEG | 628 × 628, 107 KB | `45eaa9c89e…` |
| Plata | `Pokemon Edición Plata.jpg` | JPEG | 628 × 628, 92 KB | `2441b9946c…` |
| Cristal | `Pokemon Edición Cristal.jpg` | JPEG | 1106 × 1106, 215 KB | `1839e982f5…` |
| Rubí | `Carátula de Rubí.png` | PNG | 456 × 458, 334 KB | `96d4f00e9a…` |
| Zafiro | `Carátula de Zafiro.png` | PNG | 456 × 458, 323 KB | `b45d7b2b11…` |
| Esmeralda | `Caratula Esmeralda.jpg` | JPEG | 855 × 861, 572 KB | `4808309ec0…` |
| Rojo Fuego | `Carátula de Rojo Fuego.png` | PNG | 731 × 739, 876 KB | `e728220a14…` |
| Verde Hoja | `Carátula de Verde Hoja.png` | PNG | 732 × 737, 871 KB | `7c315075af…` |

| Comprobación | Resultado |
|--------------|-----------|
| ¿Están todas? | Sí, las 11 de los juegos cargados. Rojo y Azul tienen además la versión latinoamericana (`Pokemon Rojo - LTN.png`); se usa la primera de la ficha. |
| Nombres | Sin patrón (con y sin tilde, «Carátula de…», «Pokemon Edición…»): cada uno se indica en los datos curados. |
| Cómo se obtienen | `action=query&prop=imageinfo&iiprop=url\|sha1\|timestamp` admite varios títulos en una petición y da la URL de `images.wikidexcdn.net`. |
| Licencia | Todas llevan `{{Carátula}}`: uso legítimo solo en los artículos de WikiDex (cita en ADR-0011). |
| Combates clave | `key_battle.source_page` y `source_revision` ya están en `reference.sqlite` (Brock, revisión 3562807), pero ni la API ni la web los muestran. |

## Diseño

### Datos curados

`data/curated/covers.yaml`, validado con pydantic: cada juego cargado con el título de su fichero
en WikiDex. Un juego sin entrada se carga sin portada.

```yaml
covers:
  firered: "Archivo:Carátula de Rojo Fuego.png"
  emerald: "Archivo:Caratula Esmeralda.jpg"
```

No va en `games.yaml`, como decía CA-55, porque ese fichero solo tiene las mecánicas de los
juegos objetivo y su esquema es estricto; las portadas son de los 11 juegos.

### Ingesta

- Un `CoverCache`, como `PageCache` de WikiDex:
    - **Información**: una petición a la API MediaWiki con todos los títulos que falten en la caché
      (`prop=imageinfo`), con la URL, el `sha1` y la fecha de cada fichero.
    - **Descarga**: cada portada de `images.wikidexcdn.net`, con al menos 1 s entre peticiones y el
      `User-Agent` del proyecto.
    - **Caché** en `<data-dir>/cache/wikidex/covers/`: el original, sus datos (`<juego>.json`, con
      la página, la URL y el `sha1`) y la portada reducida a 256 px con Pillow
      (`<juego>-256.png`, con `reduced` de `ingest/sources/pokeapi/sprites.py`).
    - Con `--offline`, solo la caché. Si WikiDex no responde, deja de descargar en esa carga.
- `game.cover` guarda la ruta de la portada reducida y `game.cover_source`, el título del fichero
  en WikiDex. Un juego sin portada las deja nulas.
- El informe añade «Portadas: N de M juegos» y avisa de las que faltan, con el motivo. No
  rechazan la carga.
- **`--no-covers`**: no descarga ni asigna portadas (ADR-0011).

#### Decisiones tomadas al implementar la fase 1

- **`--no-covers` en lugar de `--sin-portadas`**: las opciones de la CLI están en inglés
  (`--data-dir`, `--offline`).
- **`covers.yaml` se lee aparte** (`read_covers`, como el commit de los *sprites*), sin añadirlo a
  `CuratedData`: así las fuentes y sus tests no cambian. Se valida igual antes de empezar la
  carga.
- **Las imágenes de la carga van juntas**: `build_reference` recibe un `Images` con los *sprites*
  y las portadas, en lugar de un argumento por cada una.
- **Se comprueba el `sha1`** de cada descarga con el que da WikiDex: una página de error o una
  imagen cambiada a medias no se guarda.
- **Si cambia el título en `covers.yaml`**, la siguiente carga descarga la portada nueva: la caché
  guarda el título del que salió cada portada.
- **El test de la API usa una respuesta real** de WikiDex (solo metadatos). Detectó que la lista
  `normalized` trae un campo booleano (`fromencoded`) que el primer modelo no admitía.
- **Comprobado con red**: 11 de 11 portadas en 12,7 s la primera carga y 1,4 s las siguientes, sin
  conexión. La caché ocupa 5,6 MB. Con `--no-covers`, los 11 juegos quedan sin portada.

### Modelo de datos

| Tabla | Columnas nuevas | Notas |
|-------|-----------------|-------|
| `game` | `cover`?, `cover_source`? | `cover`, la ruta de la portada reducida relativa al directorio de datos; `cover_source`, el título del fichero en WikiDex. Nulas si no hay portada. |

`reference.sqlite` se reconstruye en cada carga: hay que repetirla, y hasta entonces la API
responde `503` pidiéndolo (`missing_columns`).

### API

- `GET /api/games/{game}/cover`: la portada en PNG, con `Cache-Control` de un día. Vale para
  cualquier juego cargado, no solo los objetivo. `404` si el juego no existe o no tiene portada.
  Reutiliza la protección de `api/services/images.py`: la ruta sale de la base de datos y queda
  dentro del directorio de datos.
- `cover_url` (o nula) y `cover_source_url` (la página del fichero en WikiDex, o nula) en
  `GameOut`, que con `?all=true` da los 11 juegos, y en `HallOfFameEntryOut`.
- **Combates clave**: el dato revisable de un combate clave da `source_url`, el enlace a la página
  de WikiDex en la revisión usada (`index.php?title=…&oldid=…`).

### Web

- Un componente `GameCover`: decorativo, caja de tamaño fijo con `object-contain` (lo aprendido en
  #65) y se oculta si no carga.
- Dónde: al elegir el juego (tarjetas), en las cabeceras de la revisión y del resultado, en el
  último juego completado del Inicio y en cada registro del *Hall of Fame*.
- El pie (`ImageNotice`) añade la titularidad y la procedencia de las portadas.
- La revisión de datos muestra, en cada combate clave, «Fuente: WikiDex» con el enlace a la
  revisión usada.

## Fases

Cada fase es un PR con sus tests y su documentación.

| Fase | Rama | Contenido | Tests |
|------|------|-----------|-------|
| 0 ✅ | `docs/portadas-juegos` | ADR-0011, este plan, comprobaciones previas, CA-55 y RF-18. | — |
| 1 ✅ | `feat/ingesta-portadas` | `covers.yaml`, `CoverCache`, `game.cover` y `cover_source`, informe, `--no-covers`. Operación de la ingesta, datos curados, modelo de datos y puesta en producción. | Sin red, con imágenes sintéticas: información y descarga, caché, `--offline`, fichero que no existe, servidor que no responde, reducción, carga con y sin portadas, `--no-covers`, esquema de `covers.yaml`. Comprobación real con red. |
| 2 | `feat/api-portadas` | Endpoint de la portada, `cover_url` y `cover_source_url`, `source_url` de los combates clave, cliente regenerado. API, Operación y manual. | `200` y `404`; ruta fuera del directorio de datos; juegos que no son objetivo; campos en los juegos, el *Hall of Fame* y la revisión. |
| 3 | `feat/web-portadas` | `GameCover` en las cinco pantallas, aviso y fuente de los combates clave. Manual de la web y CHANGELOG. | Vitest de cada pantalla con y sin portada; tamaños medidos con los datos reales. |
| 4 | `chore/release-1.2.0` | Versión 1.2.0 (MENOR) y cierre de #49. | — |

## Riesgos

| Riesgo | Mitigación |
|--------|------------|
| Licencia de WikiDex (uso legítimo solo en sus artículos). | Solo uso privado (ADR-0011), aviso con enlace a la fuente, `--no-covers`, nada en git ni redistribuido. |
| WikiDex renombra o borra un fichero. | Aviso en el informe y el juego sin portada; se corrige `covers.yaml` por PR. |
| Se vuelve a subir una portada con otra imagen. | La caché conserva la de la primera descarga y su `sha1`; para actualizarla, se borra de la caché. |
| Carga sobre WikiDex. | 12 peticiones la primera vez (una de información y once descargas), espaciadas 1 s; después, ninguna. |
| Formatos variados (JPEG, PNG, perfiles de color). | Todas se convierten a PNG RGBA con Pillow; una que no se pueda procesar es un aviso. |
| Portadas de proporciones distintas. | Caja fija con `object-contain`: se ajustan sin deformar. |
