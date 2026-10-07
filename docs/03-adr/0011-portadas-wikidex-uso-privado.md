# 0011 · Portadas de los juegos: carátulas de WikiDex, solo para uso privado

- **Estado**: Aceptado
- **Fecha**: 2026-10-06
- **Decisores**: Alberto Mercado

## Contexto

[RF-18](../01-ddf/requisitos-funcionales.md#rf-18) pide mostrar la portada de cada juego junto a
su nombre: al elegir el juego objetivo, en la revisión y el resultado, en el último juego del
Inicio y en el *Hall of Fame*, también de los juegos que no son objetivo. Como las imágenes de los
Pokémon ([ADR-0010](0010-imagenes-pokemon-cache-local.md)), se obtienen en la carga y la
aplicación funciona sin conexión.

[CA-55](../01-ddf/cuestiones-abiertas.md#resueltas) decidió sacarlas de WikiDex, que ya es fuente
de los combates clave, **si tiene la de cada juego y se pueden usar**. Lo comprobado el
2026-10-06 ([plan](../06-historial/plan-portadas.md#comprobaciones-previas)):

- WikiDex tiene la carátula de los 11 juegos cargados, la que muestra la ficha de cada artículo
  de juego. Los nombres de los ficheros no siguen un patrón (`Carátula de Rojo Fuego.png`,
  `Caratula Esmeralda.jpg`, `Pokemon Edición Oro.jpg`).
- Son JPEG o PNG de 456 a 1106 px de lado y de 84 a 876 KB, aproximadamente cuadradas.
- Todas llevan la plantilla `{{Carátula}}`, que dice:

  > Esta imagen pertenece a la cubierta o carátula de un juego u obra protegido por derechos de
  > autor. Su uso está restringido por las mismas restricciones de distribución de la obra
  > original. El uso de esta imagen se considera bajo uso de *Fair use* y su utilización en
  > cualquier lugar que no sea un artículo, bajo el único objetivo de informar, puede ser
  > considerada como violación al derecho de copia de la imagen original.

Las carátulas oficiales son de Nintendo en cualquier fuente (Bulbapedia aplica el mismo uso
legítimo), así que buscar otra no resuelve la restricción. Las imágenes de los Pokémon también son
de sus titulares, pero el repositorio de PokeAPI no añade restricciones de uso.

## Decisión

- **Se usan las carátulas de WikiDex, solo para uso privado**: la aplicación es personal, sin
  ánimo de lucro y de un solo usuario, y las portadas se descargan solo a la caché local del
  usuario, **no se versionan ni se redistribuyen** ([CA-56](../01-ddf/cuestiones-abiertas.md#resueltas))
  y se muestran con su titularidad y un enlace a su página en WikiDex.
- **Condición**: la aplicación no se publica de forma abierta. Se usa en el propio ordenador o
  con acceso privado ([ADR-0009](0009-despliegue-vm-gratuita-tailscale.md),
  [RF-19](../01-ddf/requisitos-funcionales.md#rf-19)). Si algún día se publicara, se cargan los
  datos sin portadas (`--no-covers`): la web muestra solo los nombres.
- **Qué fichero es la portada de cada juego**: se indica en un fichero curado nuevo,
  `data/curated/covers.yaml` (juego → título del fichero en WikiDex), porque los nombres no siguen
  un patrón y `games.yaml` solo tiene las mecánicas de los juegos objetivo.
- **Descarga en la ingesta**, como las páginas de WikiDex: una petición a la API MediaWiki
  (`prop=imageinfo`) para conocer la URL y el `sha1` de cada fichero, y una descarga por portada,
  con al menos 1 s entre peticiones y el `User-Agent` del proyecto. Caché permanente en
  `<data-dir>/cache/wikidex/covers/`: el original y la portada reducida a 256 px con Pillow (la
  función de ADR-0010). Para actualizar una portada, se borra de la caché.
- **Una portada que falta no rompe la carga**: el juego se muestra sin ella y el informe lo avisa.
- **`reference.sqlite`** guarda en `game` la ruta de la portada (`cover`) y su página en WikiDex
  (`cover_source`), para el enlace de la atribución.
- **La API la sirve** en `GET /api/games/{game}/cover`, para cualquier juego cargado, con la misma
  protección que las imágenes de los Pokémon (la ruta sale de la base de datos y queda dentro del
  directorio de datos), y da `cover_url` y `cover_source_url` en los juegos y el *Hall of Fame*.

## Alternativas consideradas

### No usar portadas (aplazar RF-18)

- ✅ Sin ningún riesgo de derechos.
- ❌ RF-18 queda sin hacer.

### Una portada generada por la web

El nombre del juego sobre el color de su edición (Rojo, Azul, Oro…).

- ✅ Sin imágenes de terceros, sin descargas.
- ❌ No es la portada que pide RF-18: habría que reescribir el requisito.

### Buscar otra fuente

- ✅ Podría tener una licencia más clara.
- ❌ Las carátulas oficiales son de Nintendo en cualquier sitio: es poco probable encontrar una
  fuente que permita más usos que WikiDex.

### Enlazar las portadas de WikiDex desde la web

- ✅ No se guarda ninguna copia.
- ❌ La web dependería de un servidor externo y no funcionaría sin conexión (RF-18), y cada visita
  pediría las imágenes a WikiDex.

## Consecuencias

### Positivas

- RF-18 se cumple con las portadas reales de los 11 juegos cargados.
- Reutiliza el procesado, la protección del endpoint y el componente de la web de ADR-0010.

### Negativas / riesgos

- **Riesgo de derechos aceptado**: el uso queda fuera del uso legítimo que declara WikiDex. Se
  limita a uso privado, sin redistribuir, con aviso y enlace a la fuente, y se puede quitar con
  `--no-covers`.
- La condición ata la aplicación a un uso privado: publicarla abierta exige cargar sin portadas.
- Si WikiDex renombra o borra un fichero, ese juego se queda sin portada hasta corregir
  `covers.yaml` por PR.

### Acciones derivadas

- [ ] Implementar las fases del [plan de las portadas](../06-historial/plan-portadas.md) (#49).
- [ ] Mostrar la fuente en WikiDex de cada combate clave, pendiente en
  [ADR-0004](0004-pokeapi-volcado-csv.md#acciones-derivadas), en la misma tanda.
- [x] Recordar la condición en la [puesta en producción](../05-operacion/puesta-en-produccion.md#4-codigo-web-y-datos).

## Referencias

- [Plan de las portadas](../06-historial/plan-portadas.md)
- [Plantilla:Carátula de WikiDex](https://www.wikidex.net/wiki/Plantilla:Car%C3%A1tula)
- [ADR-0010](0010-imagenes-pokemon-cache-local.md): imágenes de los Pokémon
- Issue #49
