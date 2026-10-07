# 0010 · Imágenes de los Pokémon: sprites de PokeAPI en la caché local, servidos por la API

- **Estado**: Aceptado
- **Fecha**: 2026-10-06
- **Decisores**: Alberto Mercado

## Contexto

[RF-17](../01-ddf/requisitos-funcionales.md#rf-17) pide mostrar la imagen de cada Pokémon junto
a su nombre, con una imagen propia por forma (Vulpix y Vulpix de Alola se distinguen,
[RN-05](../01-ddf/reglas-negocio.md#rn-05)), sin errores si falta alguna y con la aplicación
funcionando sin conexión una vez cargados los datos. Las cuestiones del DDF ya resueltas fijan
el marco:

- [CA-54](../01-ddf/cuestiones-abiertas.md#resueltas): se empieza con los *sprites* del
  repositorio de PokeAPI, una imagen pequeña por forma, que se descargan en la carga y sirve la
  propia aplicación: la web no pide nada a servidores externos.
- [CA-56](../01-ddf/cuestiones-abiertas.md#resueltas): las imágenes son de sus titulares; se
  guardan solo en la caché local, no se versionan en git y la aplicación muestra un aviso con su
  titularidad y su procedencia.

Lo comprobado en el repositorio [PokeAPI/sprites](https://github.com/PokeAPI/sprites) el
2026-10-06 ([plan](../06-historial/plan-imagenes.md#comprobaciones-previas)):

- Ocupa unos 10 GB: no se puede clonar ni descargar entero en cada carga.
- `sprites/pokemon/{id}.png` es un PNG de 96 × 96 px, de 0,6 a 1,1 KB, nombrado por el
  identificador numérico de la **forma** en PokeAPI (`pokemon.id` del CSV), no por el número de
  la Pokédex: Vulpix es `37.png` y Vulpix de Alola, `10103.png`. La tabla `pokemon` de
  `reference.sqlite` no guarda hoy ese identificador.
- Se puede pedir cada fichero de un commit concreto a `raw.githubusercontent.com`; una forma sin
  imagen devuelve 404.
- Su `LICENCE.txt` indica que las imágenes son *Copyright The Pokémon Company* y que el resto del
  repositorio se distribuye como CC0.

## Decisión

- **Fuente**: el *sprite* por defecto de cada forma, `sprites/pokemon/{pokeapi_id}.png` del
  repositorio PokeAPI/sprites, **fijado a un commit** igual que el volcado CSV
  ([ADR-0004](0004-pokeapi-volcado-csv.md)). El commit se guarda en
  `data/curated/pokeapi.yaml` (`sprites_commit`) y en `ingest_run`.
- **Descarga en la ingesta**, fichero a fichero, con el mismo `User-Agent` descriptivo y un
  límite de peticiones. Se guardan en una **caché permanente** por commit,
  `<data-dir>/cache/pokeapi-sprites/<commit>/<pokeapi_id>.png`, fuera de git. Con `--offline`
  solo se usa la caché.
- **Una imagen que falta no rompe la carga**: si no se puede obtener (404, error de red, fichero
  que no es un PNG), la forma se carga sin imagen y el informe lo anota como aviso. La siguiente
  carga solo descarga las que faltan.
- **`reference.sqlite` sabe qué formas tienen imagen**: la tabla `pokemon` guarda `pokeapi_id`
  y `image`, la ruta del fichero relativa al directorio de datos, o nula si no hay imagen.
- **La API sirve las imágenes** con un endpoint por forma, `GET /api/pokemon/{slug}/image`, que
  toma la ruta de la base de datos (nunca de la URL), comprueba que queda dentro del directorio
  de datos y responde 404 si no hay imagen. Las respuestas con Pokémon incluyen `image_url`, que
  es nula si la forma no tiene imagen.
- **La web muestra la imagen junto al nombre**, como imagen decorativa (`alt=""`): el nombre
  sigue identificando al Pokémon, también para los lectores de pantalla. Muestra el aviso de
  titularidad y procedencia de las imágenes.

### Ampliación tras la valoración (CA-54, 2026-10-06)

Con las imágenes ya en la web, se midió el margen de los 385 *sprites*: la figura ocupa de
mediana 56 de sus 96 px (entre 27 y 96), así que a 40 px un Pokémon típico se veía de unos 23 px.
Tras comparar las opciones en la propia web, el usuario eligió:

- **Listas: el *sprite* recortado a su figura**. La ingesta conserva el original y genera
  `trimmed/<pokeapi_id>.png` sin el margen transparente; `pokemon.image` apunta a este. Todos se
  leen bien al mismo tamaño de fila, a cambio de perder la escala relativa (Caterpie se ve tan
  grande como Gyarados).
- **Ficha: la ilustración oficial**, `sprites/pokemon/other/official-artwork/{pokeapi_id}.png`
  del mismo commit. Se reduce a 256 px al descargarla (`official-artwork-256/`), suficiente para
  mostrarla a 160 px en pantallas de alta densidad: unos 50 KB cada una en lugar de 120 KB. La
  tabla `pokemon` guarda su ruta en `artwork`, la API la sirve en
  `GET /api/pokemon/{slug}/artwork` y la ficha da `artwork_url`. Sin ilustración, la ficha
  muestra el *sprite*.
- **Pillow** pasa a ser dependencia de la aplicación, solo para procesar las imágenes en la
  ingesta. La API sirve los ficheros ya procesados.

## Alternativas consideradas

### Que la web pida las imágenes directamente a GitHub

- ✅ Sin descargas en la ingesta ni endpoint nuevo.
- ❌ La web depende de un servidor externo y no funciona sin conexión (CA-54, RF-17).
- ❌ Cada visita revela a un tercero qué Pokémon consulta el usuario.

### Versionar las imágenes en git

- ✅ Disponibles al clonar, sin descargas.
- ❌ Redistribuiría imágenes de terceros (CA-56).

### Servir el directorio de la caché como ficheros estáticos

- ✅ Sin código: un `StaticFiles` más en la API.
- ❌ La URL depende de la estructura de la caché y del identificador de PokeAPI, que son detalles
  de la ingesta, y expone un directorio entero.
- ❌ La API no puede decir qué formas tienen imagen sin mirar el disco.

### Guardar las imágenes dentro de `reference.sqlite`

- ✅ Un solo fichero, siempre coherente con los datos.
- ❌ Cada carga copiaría de nuevo todas las imágenes a la base de datos, y la caché por commit ya
  evita descargarlas otra vez.
- ❌ Mezcla datos binarios grandes con los datos de las reglas.

### Recortar el margen con CSS en lugar de en la ingesta

- ✅ Sin dependencias nuevas.
- ❌ Cada *sprite* tiene un margen distinto (la figura va de 27 a 96 px): un recorte fijo corta a
  los Pokémon grandes (el 10 % llega a 75 px o más) y no basta para los pequeños.

### Agrandar los *sprites* en las listas sin recortarlos

- ✅ Solo CSS.
- ❌ Filas más altas y los Pokémon pequeños siguen viéndose pequeños.

### Clonar o descargar el repositorio de sprites entero

- ✅ Una sola operación por commit.
- ❌ Unos 10 GB para usar menos de 1 MB.

## Consecuencias

### Positivas

- La carga es reproducible: el mismo commit da siempre las mismas imágenes, y la caché
  permanente evita volver a descargarlas.
- La web no depende de ningún servidor externo y funciona sin conexión.
- Añadir formas regionales o juegos nuevos no cambia nada: cada forma usa su `pokeapi_id`.
- El mismo mecanismo sirve después para las portadas de los juegos
  ([RF-18](../01-ddf/requisitos-funcionales.md#rf-18)) o para una imagen más grande en la ficha.

### Negativas / riesgos

- Una primera carga con conexión hace unas 800 peticiones más (el *sprite* y la ilustración de
  cada forma) y tarda unos 2 minutos y medio. Se mitiga con el límite de peticiones y la caché.
- La caché de imágenes ocupa unos 23 MB, casi todo las ilustraciones (unos 20 MB).
- Pillow es una dependencia más, compilada, que hay que mantener al día.
- `reference.sqlite` deja de ser autosuficiente: las rutas de `image` apuntan a la caché del
  mismo directorio de datos. Si se borra la caché, las formas se ven sin imagen hasta la
  siguiente carga, sin errores. Por eso, al desplegar, hay que copiar la carpeta de las imágenes
  junto con `reference.sqlite` ([puesta en producción](../05-operacion/puesta-en-produccion.md)).
- Una fuente más que fijar y actualizar: cambiar `sprites_commit` es un cambio de datos, por PR.
- Las imágenes son de terceros: se mantiene el aviso de titularidad y no se redistribuyen.

### Acciones derivadas

- [ ] Implementar las fases del [plan de imágenes de los Pokémon](../06-historial/plan-imagenes.md)
  (#49).
- [x] Valorar cómo quedan los *sprites* y si la ficha usa una imagen más grande (CA-54): ver
  la ampliación.
- [ ] Mostrar en la web el aviso de titularidad de las imágenes junto a la atribución pendiente
  de PokeAPI y WikiDex ([ADR-0004](0004-pokeapi-volcado-csv.md#acciones-derivadas)).

## Referencias

- [Plan de imágenes de los Pokémon](../06-historial/plan-imagenes.md)
- [PokeAPI/sprites](https://github.com/PokeAPI/sprites) y su
  [`LICENCE.txt`](https://github.com/PokeAPI/sprites/blob/master/LICENCE.txt)
- [ADR-0004](0004-pokeapi-volcado-csv.md): PokeAPI mediante su volcado CSV
- Issue #49
