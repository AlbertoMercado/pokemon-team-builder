# Cargar y actualizar los datos

Cómo cargar los datos de Pokémon, juegos y combates clave en la aplicación, y qué hacer si una
carga no se completa ([RF-11](../01-ddf/requisitos-funcionales.md#rf-11)). La carga la hace
el **administrador** desde la terminal, aparte de la aplicación: ni la web ni la API la lanzan
([ADR-0008](../03-adr/0008-cargas-bloqueadas.md)).

Detalle técnico (qué hace cada paso, la caché, las fuentes y las comprobaciones) en
[Operación → Ingesta de datos](../05-operacion/ingesta.md).

## Antes de empezar

- Tener el proyecto instalado con `uv sync`
  ([entorno de desarrollo](../05-operacion/entorno-desarrollo-macos.md)).
- Estar en el directorio del proyecto, en la rama `main` actualizada (`git pull`): la carga
  usa los datos curados y el commit de PokeAPI de la versión que tengas.
- Conexión a internet la primera vez. Después, la caché permite cargar sin red.

## Hacer una carga

```bash
uv run python -m ingest
```

La primera vez descarga los datos de PokeAPI, las páginas de WikiDex (WikiDex va a una petición
por segundo) y las imágenes de los Pokémon (unos 2 minutos y medio). Las siguientes usan la caché y
tardan un par de segundos.

| Opción | Para qué |
|--------|----------|
| `--offline` | Cargar sin red, solo con lo que ya está en la caché. Las imágenes que falten solo dan un aviso. |
| `--no-covers` | Cargar sin las portadas de los juegos. Hazlo si alguna vez publicas la aplicación de forma abierta: WikiDex solo permite usar sus carátulas en sus artículos ([ADR-0011](../03-adr/0011-portadas-wikidex-uso-privado.md)). |
| `--data-dir DIR` | Usar otro directorio de datos (por ejemplo, para probar sin tocar `data/`). |

Al terminar, la carga muestra un informe y sale con un código que dice cómo ha ido:

| Código | Resultado | Qué hacer |
|--------|-----------|-----------|
| `0` | **Completada**. Los datos nuevos ya están en `data/reference.sqlite`. | Reiniciar la aplicación para que los use. |
| `1` | **Error** (red, un fichero curado no válido, una comprobación fallida…). Se conservan los datos anteriores. | Leer el mensaje, corregir y repetir. Ver [errores habituales](#errores-habituales). |
| `2` | **Bloqueada**: hay algo que la aplicación no sabe tratar. Se conservan los datos anteriores. *(Disponible con la fase 7 de la ingesta; hasta entonces, estos casos salen como código 1.)* | Registrar el informe y avisar al arquitecto. Ver [carga bloqueada](#si-la-carga-queda-bloqueada). |

Para ver el código después de ejecutarla: `echo $?`.

La carga lee tus datos (`data/user.sqlite`) para comprobar que tus favoritos y tu *Hall of
Fame* siguen existiendo en los datos nuevos; si alguno no, no sustituye nada y te dice cuál
([errores habituales](#errores-habituales)). Nunca los modifica.

Los datos que confirmaste en la aplicación se conservan. Si una carga cambia el valor que se
proponía para alguno, la aplicación te lo volverá a pedir
([RN-18](../01-ddf/reglas-negocio.md#rn-18)).

## Cuándo hacer una carga nueva

- **Al instalar** la aplicación: sin carga no hay datos.
- **Al actualizar a una versión nueva** que cambia los datos curados (`data/curated/`) o el
  commit de PokeAPI. Las notas del PR lo dicen.
- **Tras resolver una carga bloqueada**, cuando la versión que la resuelve ya está en `main`.

No hace falta repetir la carga si no ha cambiado nada: daría el mismo resultado.

## Si la carga queda bloqueada

Una carga bloqueada no es un fallo tuyo ni de la carga: es una novedad en las fuentes (un
método de evolución nuevo, un juego sin combates clave…) que hay que decidir cómo tratar en
una nueva versión de la aplicación ([RF-16](../01-ddf/requisitos-funcionales.md#rf-16)).

1. **No hagas nada con los datos**: la aplicación sigue funcionando con los anteriores.
2. **Busca el informe** en `data/reports/`: dos ficheros con la fecha y `bloqueada` en el
   nombre, uno `.md` para leer y otro `.json`. El Markdown empieza con un resumen de los
   bloqueos.
3. **Regístralo en git** para avisar al arquitecto, siguiendo el
   [protocolo de registro](../05-operacion/ingesta.md#protocolo-de-registro): rama
   `chore/informe-carga-AAAA-MM-DD`, copia del informe a
   `docs/05-operacion/informes-carga/`, una fila con estado «abierta» en
   [Informes de carga](../05-operacion/informes-carga/index.md) y un PR. La carga nunca
   sube nada a git por su cuenta.
4. **Espera a la nueva versión**. Cuando el arquitecto la publique en `main`, actualiza tu
   copia (`git pull`) y repite la carga.

## Errores habituales

| Mensaje | Causa | Solución |
|---------|-------|----------|
| `ERROR en los datos curados; no se ha cargado nada.` | Un fichero de `data/curated/` no es válido (una errata, un campo que falta…). | El mensaje dice el fichero y el motivo. Si no lo has tocado tú, avisa al arquitecto. |
| Error de red o de descarga | Sin conexión, o PokeAPI o WikiDex no responden. | Repetir más tarde, o usar `--offline` si la caché está completa. |
| `Comprobación fallida: …` | Los datos cargados no son los esperados (por ejemplo, faltan especies). | No es algo que se arregle en local: avisa al arquitecto con el mensaje. |
| `Datos del usuario: Favoritos que no existen en la nueva carga: …` | Tienes en favoritos una forma que la nueva carga ya no tiene. | Quítala de favoritos (`DELETE /api/favorites/{pokemon}`) y repite la carga. Si es un Pokémon que debería seguir existiendo, avisa al arquitecto. |
| `Datos del usuario: Registros del Hall of Fame con …` | Un registro de tu *Hall of Fame* usa un juego o un Pokémon que la nueva carga ya no tiene. El número es el `id` del registro. | Corrige o elimina ese registro (`PATCH` o `DELETE /api/hall-of-fame/{id}`) y repite la carga. |
| Aviso `N juegos sin portada, …` | No se ha podido obtener la portada de esos juegos: sin conexión, WikiDex no responde o ha cambiado el nombre del fichero. | Nada: la carga se completa y esos juegos se muestran sin portada. Si el aviso dice que el fichero no está en WikiDex, avisa al arquitecto para corregir `data/curated/covers.yaml`. |
| Aviso `N formas sin imagen, …` | No se ha podido obtener la imagen de esas formas: sin conexión, el servidor de imágenes no responde o no la tiene. | Nada: la carga se completa y esas formas se muestran sin imagen. Repite la carga con conexión para descargar las que falten. |
| Aviso `Confirmaciones de datos que ya no existen…` | Confirmaste datos que la nueva carga ya no tiene. | Nada: la carga se completa y esas confirmaciones se ignoran. |

## Consultar los datos cargados

Para ver qué hay en la base de datos sin abrir la aplicación:

```bash
uvx datasette data/reference.sqlite
```

Más opciones y consultas de ejemplo en
[Operación → Consultar los datos](../05-operacion/ingesta.md#consultar-los-datos).
