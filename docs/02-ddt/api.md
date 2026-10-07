# API

Convenciones y decisiones de diseño de la API HTTP, servida por FastAPI bajo el prefijo `/api`.

- **Qué endpoints hay, sus parámetros, respuestas y campos**: la
  [referencia de la API](api-referencia.md), generada del código
  ([ADR-0012](../03-adr/0012-referencia-api-desde-openapi.md)). El mismo contrato OpenAPI genera
  el cliente de la web ([ADR-0007](../03-adr/0007-cliente-generado-openapi.md)).
- **Cómo se usa**, con ejemplos: el [manual de la API](../04-manual-usuario/api.md).
- **Cómo se arranca**: [Operación](../05-operacion/api.md).

## Convenciones

- JSON en peticiones y respuestas, con nombres de campo en `snake_case`.
- Los recursos se identifican con las claves naturales del
  [modelo de datos](modelo-datos.md) (`firered`, `vulpix-alola`, `RN-07`).
- Los errores usan el formato por defecto de FastAPI (`{"detail": ...}`). `detail` es un texto,
  salvo en los `422` de validación de FastAPI (una lista) y en dos `409`, que son un objeto con
  el mensaje: el de los datos pendientes, con esos datos (`PendingDataOut`), y el de un juego ya
  registrado en el *Hall of Fame*, con su registro (`CompletedGameOut`,
  [CA-68](../01-ddf/cuestiones-abiertas.md#resueltas)). Cada endpoint dice en su descripción
  cuándo responde cada código:
    - `404`: el recurso no existe.
    - `409`: la operación no se puede hacer en el estado actual (p. ej., generar con datos sin
      confirmar).
    - `422`: datos de entrada no válidos.
    - `503`: todavía no se han cargado los datos de referencia (`reference.sqlite`), o los cargó
      una versión anterior de la aplicación y les faltan tablas o columnas: hay que repetir la
      carga.
- Sin autenticación: la aplicación es de un solo usuario.
- **Tipos actuales y tipos en el juego**: el catálogo y los favoritos dan los tipos de la última
  generación cargada (hoy, la 3.ª: Clefairy es Normal); la generación, la revisión y el
  *Hall of Fame* usan los del juego ([RN-10](../01-ddf/reglas-negocio.md#rn-10)).

## Catálogo

- Las formas regionales son entradas propias
  ([RN-05](../01-ddf/reglas-negocio.md#rn-05)): `vulpix` y `vulpix-alola`, «Vulpix de Alola».
- **Evoluciones**: cada una se da con el disparador y las condiciones de PokeAPI tal como los
  guarda la ingesta ([modelo de datos](modelo-datos.md#evoluciones)). Como el método puede
  cambiar entre juegos, se da el del grupo de versiones más reciente cargado que tiene esa
  evolución. La web traduce el disparador y las condiciones a texto.

## Imágenes y portadas

Las imágenes de los Pokémon ([ADR-0010](../03-adr/0010-imagenes-pokemon-cache-local.md)) y las
portadas de los juegos ([ADR-0011](../03-adr/0011-portadas-wikidex-uso-privado.md)) las descarga
la carga de datos a la caché local, y la API las sirve, así que la web no pide nada a servidores
externos:

- **URLs en las respuestas**: `image_url` y `artwork_url` en las formas, y `cover_url` en los
  juegos y el *Hall of Fame*, o `null` si no hay. La web no construye URLs: solo muestra la
  imagen si viene la suya ([RF-17](../01-ddf/requisitos-funcionales.md#rf-17),
  [RF-18](../01-ddf/requisitos-funcionales.md#rf-18)).
- **`cover_source_url`**: la página de cada portada en WikiDex, para el aviso de su titularidad
  ([CA-56](../01-ddf/cuestiones-abiertas.md#resueltas)). La API solo construye el enlace; nunca
  pide nada a WikiDex.
- **Caché del navegador**: los PNG se sirven con `Cache-Control: public, max-age=86400`, así que
  no se vuelven a pedir durante un día.
- **Rutas seguras**: la ruta del fichero sale de `reference.sqlite`, nunca de la URL, y se
  comprueba que queda dentro del directorio de datos. Si el fichero ya no está (porque se borró
  la caché), la respuesta es `404` y la web muestra solo el nombre.

## Reglas

`user.sqlite` solo guarda las reglas que el usuario ha cambiado; el resto usa los valores por
defecto del catálogo ([CA-41](../01-ddf/cuestiones-abiertas.md#resueltas)).

## Revisión de datos

- **Qué datos intervienen** lo decide `core.review.involved_facts`
  ([motor](motor.md#revision-de-datos-corereviewpy)): las mecánicas del juego, sus combates
  clave si [RN-17](../01-ddf/reglas-negocio.md#rn-17) está activa y la existencia y la llegada de
  cada favorito que no esté ya descartado con datos conocidos. De ellos, la revisión muestra los
  que la carga dejó **inferidos** o **pendientes**; los automáticos no se revisan.
- **Orden**: primero los del juego (mecánicas, combates clave) y después los de cada favorito en
  orden de la Pokédex Nacional, la existencia antes que la llegada.
- **Confirmaciones**: cada una guarda el *hash* de la propuesta a la que respondió
  ([modelo de datos](modelo-datos.md#implementacion-de-usersqlite)). Una corrección del usuario
  se mantiene mientras la carga proponga lo mismo; si propone otra cosa, el dato vuelve a estar
  pendiente ([RN-18](../01-ddf/reglas-negocio.md#rn-18)).
- Se puede confirmar cualquier dato revisable del juego, intervenga o no ahora: si después se
  añade el favorito, ya está confirmado.

## Generación

- **Sin estado**: la generación no se guarda; con los mismos datos da siempre la misma respuesta.
  Si queda algún dato sin confirmar que interviene, responde `409` con los mismos datos que
  muestra la revisión.
- **Puntuaciones enteras** ([CA-51](../01-ddf/cuestiones-abiertas.md#resueltas)): el motor
  calcula con fracciones exactas ([ADR-0006](../03-adr/0006-algoritmo-busqueda-exacta.md)) y
  decide con ellas el orden y los empates. La API redondea la puntuación de cada equipo al entero
  más cercano (las mitades, hacia arriba) y reparte las aportaciones con el **método del mayor
  resto**: cada regla recibe la parte entera de su aportación y las unidades que faltan para el
  total van a las de mayor parte decimal (a igualdad, a la primera del catálogo). Así siempre
  suman la puntuación del equipo. Por ejemplo, con una puntuación exacta de 223/12 (18,58) en la
  que RN-17 aporta 9,58, RN-17 recibe la unidad que falta y se muestra 1 + 3 + 10 + 5 = 19. Lo
  que aporta cada sugerencia (`gain`) también se redondea. Dos equipos que se muestran con el
  mismo número no tienen por qué estar empatados.
- **Comprobar un equipo elegido** (`team-checks`): la usa el selector del resultado antes de
  registrar el equipo ([motor](motor.md#comprobacion-de-un-equipo-elegido-corerulescheckpy)).
  No se guarda, y el registro en el *Hall of Fame* no exige que el equipo cumpla las reglas.

## Hall of Fame

- **Recorrido**: los registros se ordenan por fecha y, a igualdad, por orden de registro
  ([RF-12](../01-ddf/requisitos-funcionales.md#rf-12)). Con el filtro `game`, `order` sigue
  siendo la posición en el recorrido completo.
- **Juegos**: se puede registrar cualquier juego cargado, también los que no son juego objetivo
  (Rojo, Oro…), porque todos forman parte del recorrido.
- **Tipos**: cada miembro guarda una copia de sus tipos en la generación de ese juego
  ([CA-07](../01-ddf/cuestiones-abiertas.md#resueltas)): Magneton es Eléctrico en Rojo y
  Eléctrico/Acero en Rojo Fuego. Un Pokémon que no existe en la generación del juego no se puede
  registrar.
- **Exclusiones**: al revisar los datos y al generar, el recorrido se pasa al motor, que excluye
  las líneas ya usadas según [RN-16](../01-ddf/reglas-negocio.md#rn-16). Corregir o eliminar un
  registro cambia las exclusiones desde la siguiente petición.
